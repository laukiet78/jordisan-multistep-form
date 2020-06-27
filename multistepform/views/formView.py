from django.http import HttpResponse
from django.shortcuts import render
from django.forms.models import model_to_dict
from django.shortcuts import redirect

from ..forms.messageForm import MessageForm
from ..forms.customerForm import CustomerForm
from ..forms.surveyForm import SurveyForm

from general.models.customer import Customer

def FormView(request, step=1):
    ''' View for multiple steps form '''
    
    STEPS = {
        1: {
            'form': 'SurveyForm'
        },
        2: {
            'form': 'MessageForm'
        },
        3:  {
            'form': 'CustomerForm'
        }
    }
    
    SESSIONKEY_PREFIX = 'multistepform_step_'

    form = globals()[STEPS[step]['form']]() # default form for current step

    if request.method == 'POST':
        if step == len(STEPS):
            # last step => save in database

            form = globals()[STEPS[step]['form']](request.POST)
            # check that user is not already on the database
            if form.is_valid():
                existing_customers = Customer.objects.filter(email=form.instance.email)
                if existing_customers.count() > 0:
                    # customer already exists => update data
                    existing_customer = existing_customers[0]
                    existing_customer.first_name = form.instance.first_name
                    existing_customer.last_name = form.instance.last_name
                    existing_customer.phone_number = form.instance.phone_number
                    form.instance = existing_customer
                    form.instance.save()
                else:
                    form.save() # save new customer

                # retrieve previous forms (stored in session) and save them
                for i in range(1, len(STEPS)):
                    form_stored = globals()[STEPS[i]['form']](request.session.get(SESSIONKEY_PREFIX + str(i)))
                    form_stored.instance.customer = form.instance # set saved customer in related entities
                    form_stored.save()

                request.session.flush() # remove session data
                return render(request, 'multistepform/feedback.html', {
                    'page_title': 'Thanks',
                    'msg': 'Your data has been saved. We will contact you soon.'
                })

        else:
            # not last step => store data in session (temporarily) using model_to_dict to make it serializable

            form = globals()[STEPS[step]['form']](request.POST)
            if form.is_valid():
                request.session[SESSIONKEY_PREFIX + str(step)] = model_to_dict(form.instance)
                return redirect('/step/' + str(step + 1))

    else:
        # GET => try to get data from session (in case it was previously stored)
        form = globals()[STEPS[step]['form']](request.session.get(SESSIONKEY_PREFIX + str(step)))  

    return render(request, 'multistepform/form.html', {
        'page_title': 'Multiple steps form (' + str(step) + '/' + str(len(STEPS)) + ')',
        'form': form,
        'step': step,
        'step_last': len(STEPS)
    })