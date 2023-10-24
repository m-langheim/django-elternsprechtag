from authentication.models import CustomUser
from dashboard.models import Event
from django.db.models import Q
import pytz

# pdf gen
from io import BytesIO
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import datetime
from reportlab.lib.units import cm, mm, inch
from django.utils import timezone
from reportlab.pdfgen import canvas


class EventPDFExport:
    def __init__(self, user_id, buffer=BytesIO(), pagesize="A4") -> None:
        self.buffer = buffer
        if pagesize == "A4":
            self.pagesize = A4
        elif pagesize == "Letter":
            self.pagesize = letter
        try:
            self.user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise ("Error could not generate the PDF")
        self.width, self.height = self.pagesize

    def _header_footer(self, canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()

        # Header
        header_style = ParagraphStyle(
            "header_style",
            alignment=TA_CENTER,
        )
        header = Paragraph(
            str(datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
            + "_"
            + str(self.user.first_name)
            + " "
            + str(self.user.last_name),
            header_style,
        )
        w, h = header.wrap(doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)

        # Footer
        footer_style = ParagraphStyle(
            "footer_style", alignment=TA_CENTER, textColor="red"
        )
        footer = Paragraph("Alle Angaben sind ohne Gewähr.", footer_style)
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)

        # Release the canvas
        canvas.restoreState()

    def print_events(self):
        user = self.user
        if user.role == 0 or user.role == 1:
            buff = BytesIO()
            doc = SimpleDocTemplate(
                buff,
                pagesize=A4,
                rightMargin=2 * cm,
                leftMargin=2 * cm,
                topMargin=3 * cm,
                bottomMargin=2 * cm,
                title="Export Events",
            )
            styles = getSampleStyleSheet()
            elements = []

            if user.role == 0:
                events = Event.objects.filter(Q(parent=user))
            else:
                events = Event.objects.filter(Q(teacher=user))

            if events.count() == 0:
                no_events_style = ParagraphStyle(
                    "no_events_style",
                    alignment=TA_CENTER,
                )
                elements.append(
                    Paragraph("Sie haben bisher keine Events", no_events_style)
                )
            else:
                dates = []

                datetime_objects = events.order_by("start").values_list(
                    "start", flat=True
                )
                for datetime_object in datetime_objects:
                    if timezone.localtime(datetime_object).date() not in [
                        date.date() for date in dates
                    ]:
                        dates.append(datetime_object.astimezone(pytz.UTC))

                events_dct = {}
                for date in dates:
                    events_dct[str(date.date())] = Event.objects.filter(
                        Q(
                            start__gte=timezone.datetime.combine(
                                date.date(),
                                timezone.datetime.strptime(
                                    "00:00:00", "%H:%M:%S"
                                ).time(),
                            )
                        ),
                        Q(
                            start__lte=timezone.datetime.combine(
                                date.date(),
                                timezone.datetime.strptime(
                                    "23:59:59", "%H:%M:%S"
                                ).time(),
                            )
                        ),
                    ).order_by("start")

                date_style = ParagraphStyle(
                    "date_style",
                    fontName="Helvetica-Bold",
                    fontSize=14,
                    spaceBefore=7,
                    spaceAfter=3,
                )

                for date in dates:
                    elements.append(
                        Paragraph(str(date.date().strftime("%d.%m.%Y")), date_style)
                    )
                    elements.append(Spacer(0, 5))

                    events_per_date = events.filter(
                        Q(
                            start__gte=timezone.datetime.combine(
                                date.date(),
                                timezone.datetime.strptime(
                                    "00:00:00", "%H:%M:%S"
                                ).time(),
                            )
                        ),
                        Q(
                            start__lte=timezone.datetime.combine(
                                date.date(),
                                timezone.datetime.strptime(
                                    "23:59:59", "%H:%M:%S"
                                ).time(),
                            )
                        ),
                    ).order_by("start")
                    for event_per_date in events_per_date:
                        t = str(
                            timezone.localtime(event_per_date.start)
                            .time()
                            .strftime("%H:%M")
                        )
                        s = ""
                        if len(event_per_date.student.all()) == 0:
                            s = "/"
                        else:
                            for student in event_per_date.student.all():
                                s += "{} {}; ".format(
                                    student.first_name, student.last_name
                                )
                            s = s[:-2]

                        b = ""
                        if event_per_date.status == 2:
                            b = "| Nicht bestätigt"

                        elements.append(Paragraph(f"{t}  |  {s} {b}", styles["Normal"]))
                        elements.append(Spacer(0, 5))

                doc.build(
                    elements,
                    onFirstPage=self._header_footer,
                    onLaterPages=self._header_footer,
                    canvasmaker=NumberedCanvas,
                )

                buff.seek(0)
                return buff


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.Canvas = canvas.Canvas
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            # pdb.set_trace()
            # self.setFont('Arial', 8)
            self.draw_page_number(num_pages)
            self.Canvas.showPage(self)
        self.Canvas.save(self)

    def draw_page_number(self, page_count):
        # Change the position of this to wherever you want the page number to be
        self.drawCentredString(
            100 * mm,
            15 * mm + (0.2 * inch),
            "Seite %d von %d" % (self._pageNumber, page_count),
        )
