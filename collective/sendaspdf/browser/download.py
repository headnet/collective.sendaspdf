# coding: utf-8
from plone.i18n.normalizer import filenamenormalizer
from Products.CMFCore.utils import getToolByName
from collective.sendaspdf.browser.base import BaseView


class PreDownloadPDF(BaseView):
    """ This page is the one called when clicking on the
    'Download as PDF' view.
    It generates the PDF file then redirects to the real
    download view (see below).
    """
    def __call__(self):
        self.make_pdf()
        if self.errors:
            return self.index(self)

        self.request.form['pdf_name'] = self.filename
        return self.context.restrictedTraverse('@@send_as_pdf_download')()


def convert_danish_chars(text):
    text = text.replace('å', 'aa').replace('æ', 'ae').replace('ø', 'oe')
    text = text.replace('Å', 'Aa').replace('Æ', 'Ae').replace('Ø', 'Oe')
    return text

class DownloadPDF(BaseView):
    """ View called when clicking the 'Click here to preview'
    link.
    """
    def generate_pdf_name(self):
        """ Generates the name for the PDF file.
        Very application specific /SBW
        """
        name = self.context.getId()
        hastitle = False
        if self.context.Title():
            hastitle = True
            name += ' - '
            name += filenamenormalizer.normalize(convert_danish_chars(self.context.Title()))

        try:
            if self.context.answer:
                name += ' - '
                transforms = getToolByName(self.context, 'portal_transforms')
                stream = transforms.convertTo('text/plain', self.context.answer.output, mimetype='text/html')
                text = stream.getData().strip()
                text = text.replace('\r', '')
                text = text.replace('\n', '')
                text = filenamenormalizer.normalize(convert_danish_chars(text))
                if hastitle:
                    text = text[0:60]
                else:
                    text = text[0:80]
                name += text
        except AttributeError:
            pass

        return '%s.pdf' % name

    def __call__(self):
        form = self.request.form
        self.check_pdf_accessibility()

        if self.errors:
            return self.index(self)

        self.pdf_file = file('%s/%s' % (self.tempdir,
                                        form['pdf_name']),
                             'r')
        self.request.response.setHeader("Content-type",
                                        "application/pdf")
        self.request.response.setHeader("X-Robots-Tag",
                                        "noindex")
        self.request.response.setHeader("Cache-Control",
                                        "no-cache, must-revalidate")

        user_agent = self.request['HTTP_USER_AGENT']
        if not self.pdf_tool.is_browser_excluded(user_agent):
            disposition = ('attachment; filename="%s"' %
                           self.generate_pdf_name())
            self.request.response.setHeader('Content-Disposition', disposition)

        return self.pdf_file.read()
