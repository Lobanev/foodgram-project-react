from datetime import date
from io import BytesIO
from rest_framework import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from django.core.files.base import ContentFile

import base64


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class PDFGenerator:
    def __init__(self, filename: str, fontname: str = 'Bonche-Light',
                 fontpath: str = 'Bonche-Light.ttf',
                 pagesize: tuple = landscape(letter)):
        self.buffer = BytesIO()
        self.filename = filename
        self.fontname = fontname
        self.fontpath = fontpath
        self.pagesize = pagesize
        self.canvas = None

    def _register_font(self):
        pdfmetrics.registerFont(TTFont(self.fontname, self.fontpath, 'UTF-8'))

    def _draw_header(self, text: str, size: int = 20, x: int = 250,
                     y: int = 600):
        self.canvas.setFont(self.fontname, size)
        self.canvas.drawString(x, y, text)

    def _draw_body(self, text_list: list, size: int = 14,
                   x: int = 75, y: int = 560,
                   line_step: int = 20):
        self.canvas.setFont(self.fontname, size)
        for text in text_list:
            self.canvas.drawString(x, y, text)
            y -= line_step

    def _draw_footer(self, text: str, size: int = 10,
                     x: int = 255, y: int = 50):
        self.canvas.setFont(self.fontname, size)
        self.canvas.drawString(x, y, text)

    def _create_canvas(self):
        self.canvas = Canvas(self.buffer, pagesize=self.pagesize)

    def _close_canvas(self):
        self.canvas.showPage()
        self.canvas.save()

    def generate(self, text_list: list):
        self._register_font()
        self._create_canvas()
        self._draw_header('SHOP LIST')
        self._draw_body(text_list)
        self._draw_footer(f'© FoodGram {date.today().year}')
        self._close_canvas()

        self.buffer.seek(0)
        return self.buffer

    def download_pdf(self, request):
        shopping_list = request.GET.get('items')
        if not shopping_list:
            return HttpResponseBadRequest('Parameter <items> is required.')

        pdf_generator = PDFGenerator('shopping_list.pdf')
        pdf_buffer = pdf_generator.generate(shopping_list.split('\n'))

        response = HttpResponse(pdf_buffer.read(),
                                content_type='application/pdf')
        response['Content-Disposition'] = f'attachment;' \
                                          f'filename={pdf_generator.filename}'
        return response
