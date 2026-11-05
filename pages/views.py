from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render

from .models import ContactMessage, WhyChooseItem


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


def about(request):
    return render(request, 'pages/about.html', {'values': WhyChooseItem.objects.filter(place='about')})


def how_to_pay(request):
    return render(request, 'pages/how_to_pay.html')


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thanks for reaching out — our team will get back to you shortly.')
        return redirect('pages:contact')
    return render(request, 'pages/contact.html', {'form': form})
