from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from django.urls import reverse
from django.conf import settings
from django.contrib import messages

import json

# Create your views here.
class IndexView(View):

    def get(self, request):  
        return render(request, 'engine/index.html')
    

    def post(self, request):
        if 'file' not in request.FILES:
            messages.add_message(request, messages.INFO, 'No file given. Please select the CV and click Score.')
            return HttpResponseRedirect(reverse('engine:index'))
        file = request.FILES['file']
        if not self.validate_file(file):
            messages.add_message(request, messages.INFO, 'Invalid file given. Please use docx or pdf format only.')
            return HttpResponseRedirect(reverse('engine:index'))
        
        file_name = self.handle_uploaded_file(file)

        from engine.core.parser import CVParser
        parser = CVParser(file_name)
        parsed_data = parser.parsed_data
        #print(parsed_data)
        return render(request, 'engine/index.html', {'parsed_data':parsed_data})
    

    def validate_file(self, file):
        if file.content_type not in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return False
        else:
            return True

    
    def handle_uploaded_file(self, f):
        file_name = settings.BASE_DIR+'/engine/core/uploads/'+f.name
        with open(file_name, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        return file_name