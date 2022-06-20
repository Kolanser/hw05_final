from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма записи и изменения поста"""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        text = self.cleaned_data['text']
        if not text:
            raise forms.ValidationError('Пост не может быть пустым')
        return text


class CommentForm(forms.ModelForm):
    """Форма добавления комментария"""
    class Meta:
        model = Comment
        fields = ('text',)
