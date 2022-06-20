from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Статичная информация об авторе"""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Статичная информация о технологиях"""
    template_name = 'about/tech.html'
