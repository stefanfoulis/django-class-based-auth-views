=============================
django-class-based-auth-views
=============================

related packages
================

* `django-password-reset <https://github.com/brutasse/django-password-reset>`_ has class based views to reset
  forgotten passwords by email confirmation.


A reimplementation of ``django.contrib.auth.views`` as class based views. Hopefully at some point this project or
something similar will make it into django proper.

Currently ``LoginView`` and ``LogoutView`` are implemented.


Installation
============

::

    pip install django-class-based-auth-views


Basic usage
===========

Instead of including ``django.contrib.auth.login`` into your ``urls.py``, just use the one provided by this project.
``urls.py``::

    from class_based_auth_views.views import LoginView
    urlpatterns = patterns('',
        url(r'^login/$', LoginView.as_view(form_class=EmailAsUsernameAuthenticationForm), name="login"),
        url(r'^logout/$', LogoutView.as_view(), name="logout"),
    )


Be aware that the logout view requires a ``POST`` to actually logout. So the ``registration/logout.html`` template
should contain a form with a submit button.


Extending LoginView Example
===========================

Now that LoginView is based on generic class based views it is much easier to extend. Say you need to implement a
2 step login procedure with a one time password::


    from django.contrib.auth import login

    class PhaseOneLoginView(LoginView):
        def form_valid(self, form):
            """
            Forces superusers to login in a 2 step process (One Time Password). Other users are logged in normally
            """
            user = form.get_user()
            if user.is_superuser:
                self.save_user(user)
                return HttpResponseRedirect(self.get_phase_two_url())
            else:
                login(self.request, user)
                return HttpResponseRedirect(self.get_success_url())

        def get_phase_two_url(self):
            return reverse('phase_two_login')

        def save_user(self, user):
            self.request.session['otp_user'] = user


    class PhaseTwoLoginView(FormView):
        form_class = OTPTokenForm

        def get_user(self):
            return self.request.session.get('otp_user', None)

        def clean_user(self):
            if 'otp_user' in self.request.session:
                del self.request.session['otp_user']

        def form_valid(self, form):
            code = form.cleaned_data.get('code')
            user = self.get_user()
            login(request, user)
