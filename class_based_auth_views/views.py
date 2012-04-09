#-*- coding: utf-8 -*-
"""
Class based alternatives for the generic Django auth views. These should be
easier to extend than the function-based generic auth views, and are in
keeping with the transition to class based views in Django 1.3
"""

import urlparse
from django.core.urlresolvers import reverse
from django.utils.functional import lazy
from django.contrib.auth import REDIRECT_FIELD_NAME, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.http import base36_to_int
from django.contrib.auth.tokens import default_token_generator
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateResponseMixin, TemplateView
from django.conf import settings
from django.contrib.sites.models import get_current_site

reverse_lazy = lazy(reverse, str)


class CurrentAppMixin(TemplateResponseMixin):
    """
    Mixin to add give the option of adding the current_app to the context.
    Returns RequestContext objects (assuming context isn't already a Context
    object)
    """
    def render_to_response(self, context, **response_kwargs):
        response_kwargs['current_app'] = self.current_app
        return super(CurrentAppMixin, self).render_to_response(context,
                                                          **response_kwargs)


class LoginView(FormView, CurrentAppMixin):
    """
    Class based version of django.contrib.auth.views.login

    Usage:
        in urls.py:
            url(r'^login/$',
                LoginView.as_view(
                    form_class=MyCustomAuthFormClass,
                    success_url='/my/custom/success/url/),
                name="login"),

    """
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = 'registration/login.html'
    current_app = None

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        self.set_test_cookie()
        return super(LoginView, self).get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.check_and_delete_test_cookie()
        return super(LoginView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())
    
    def form_invalid(self, form):
        self.set_test_cookie()
        return super(LoginView, self).form_invalid(form)

    def get_success_url(self):
        redirect_to = self.success_url or \
                  self.request.REQUEST.get(self.redirect_field_name, '')

    # Use default if redirect_to is empty or has a different host
    # (security check)
        netloc = urlparse.urlparse(redirect_to)[1]
        if not redirect_to or (netloc and netloc != self.request.get_host()):
            redirect_to = settings.LOGIN_REDIRECT_URL
        return redirect_to

    def get_context_data(self, **kwargs):
        kwargs['site'] = get_current_site(self.request)
        kwargs['site_name'] = kwargs['site'].name
        return super(LoginView, self).get_context_data(**kwargs)

    def set_test_cookie(self):
        self.request.session.set_test_cookie()

    def check_and_delete_test_cookie(self):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
            return True
        return False


class LogoutView(TemplateView, CurrentAppMixin):
    """
    Class based version of django.contrib.auth.views.logout
    """
    next_page = None
    template_name = 'registration/logged_out.html'
    redirect_field_name = REDIRECT_FIELD_NAME
    current_app = None

    def get(self, request, *args, **kwargs):
        logout(self.request)
        redirect_to = request.REQUEST.get(self.redirect_field_name, '')
        if redirect_to:
            netloc = urlparse.urlparse(redirect_to)[1]
            # Security check -- don't allow redirection to a different host.
            if not (netloc and netloc != self.request.get_host()):
                return HttpResponseRedirect(redirect_to)
        if self.next_page:
            return HttpResponseRedirect(self.next_page)
        return super(LogoutView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['redirect_field_name'] = self.get_success_url()
        kwargs['site'] = get_current_site(self.request)
        kwargs['site_name'] = kwargs['site'].name
        return super(LogoutView, self).get_context_data(**kwargs)


class PasswordResetView(FormView, CurrentAppMixin):
    """
    Class based version of django.contrib.auth.views.password_reset
    """
    form_class = PasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    is_admin_site = False
    token_generator = default_token_generator
    post_reset_redirect = reverse_lazy('django.contrib.auth.views.password_reset_done')
    from_email = None
    current_app = None

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(PasswordResetView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        User has entered an email address of a valid user (checked by PasswordResetForm)
        """
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'request': self.request,
        }
        if self.is_admin_site:
            opts = dict(opts, domain_override=self.request.META['HTTP_HOST'])
        form.save(**opts)
        return HttpResponseRedirect(self.post_reset_redirect)


class PasswordResetConfirmView(FormView, CurrentAppMixin):
    """
    Class based version of django.contrib.auth.views.password_reset_confirm
    """
    uidb36 = None
    token = None
    template_name = 'registration/password_reset_confirm.html'
    token_generator = default_token_generator
    form_class = SetPasswordForm
    post_reset_redirect = reverse_lazy('django.contrib.auth.views.password_reset_complete')
    current_app = None

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_link(kwargs['uidb36'], kwargs['token']):
            self.request = request
            return self.render_to_response(self.get_context_data(form=None))
        return super(PasswordResetConfirmView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['validlink'] = self.validlink
        return super(PasswordResetConfirmView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.post_reset_redirect)

    def get_form_kwargs(self):
        kwargs = super(PasswordResetConfirmView, self).get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def check_link(self, uidb36, token):
        assert uidb36 is not None and token is not None # checked by URLconf
        try:
            uid_int = base36_to_int(uidb36)
            self.user = User.objects.get(id=uid_int)
        except (ValueError, User.DoesNotExist):
            self.user = None
        self.validlink = bool(self.user is not None and self.token_generator.check_token(self.user, token))
        return self.validlink