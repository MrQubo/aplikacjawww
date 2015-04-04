#-*- coding: utf-8 -*-
from django.forms import ModelForm
from django.contrib.auth.models import User

from django_select2 import ModelSelect2MultipleField, Select2MultipleWidget, ModelSelect2Field, Select2Widget

from wwwapp.models import UserProfile, Article, Workshop, WorkshopCategory, WorkshopType


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['gender', 'school', 'matura_exam_year', 'how_do_you_know_about', 'interests']
        labels = {
            'gender': u'Płeć',
            'school': u'Szkoła lub uniwersytet',
            'matura_exam_year': u'Rok zdania matury',
            'how_do_you_know_about': u'Skąd wiesz o WWW?',
            'interests': 'Zainteresowania',
        }


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': u'Imię',
            'last_name': u'Nazwisko',
            'email': u'E-mail',
        }


class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'name', 'on_menubar', 'content']
        labels = {
            'title': u'Tytuł',
            'name': u'Nazwa (w URLach)',
            'on_menubar': u'Umieść w menu',
            'content': u'Treść',
        }
    
    def __init__(self, user, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        if not user.has_perm('wwwapp.can_put_on_menubar'):
            del self.fields['on_menubar']


class WorkshopForm(ModelForm):
    category = ModelSelect2MultipleField(label="Kategorie", queryset=WorkshopCategory.objects, required=False, 
                                         widget=Select2MultipleWidget(select2_options={'width': '200px',})
                                         )
    category.help_text = "" # this removes annoying message ' Hold down "Control", or "Command" (..) '
    type = ModelSelect2Field(label="Rodzaj zajęć", queryset=WorkshopType.objects, required=False, 
                             widget=Select2Widget(select2_options={'width': '200px',})
                             )
    class Meta:
        model = Workshop
        fields = ['title', 'name', 'type', 'category', 'proposition_description']
        labels = {
            'title': u'Tytuł',
            'name': u'Nazwa (w URLach)',
            'proposition_description': u'Opis propozycji warsztatów',
        }
