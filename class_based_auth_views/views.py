#-*- coding: utf-8 -*-
import urlparse
from django.core.urlresolvers import reverse
from django.utils.functional import lazy
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.http import base36_to_int
from django.contrib.auth.tokens import default_token_generator
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateResponseMixin
from django.conf import settings

reverse_lazy = lazy(reverse, str)


class LoginView(FormView):
    """
    This is a class based version of django.contrib.auth.views.login.

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

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        The user has provided valid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        can log him in.
        """
        login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.success_url:
            redirect_to = self.success_url
        else:
            redirect_to = self.request.REQUEST.get(self.redirect_field_name, '')

        netloc = urlparse.urlparse(redirect_to)[1]
        if not redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL
        # Security check -- don't allow redirection to a different host.
        elif netloc and netloc != self.request.get_host():
            redirect_to = settings.LOGIN_REDIRECT_URL
        return redirect_to

    def set_test_cookie(self):
        self.request.session.set_test_cookie()

    def check_and_delete_test_cookie(self):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
            return True
        return False

    def get(self, request, *args, **kwargs):
        """
        Same as django.views.generic.edit.ProcessFormView.get(), but adds test cookie stuff
        """
        self.set_test_cookie()
        return super(LoginView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Same as django.views.generic.edit.ProcessFormView.post(), but adds test cookie stuff
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            self.check_and_delete_test_cookie()
            return self.form_valid(form)
        else:
            self.set_test_cookie()
            return self.form_invalid(form)

class CurrentAppMixin(TemplateResponseMixin):
    """
    Mixin to add give the option of adding the current_app to the context. Returns RequestContext
    objects (assuming context isn't already a Context object)
    """
    def render_to_response(self, context, **response_kwargs):
        response_kwargs['current_app'] = self.current_app
        return super(CurrentAppMixin, self).render_to_response(context, **response_kwargs)

class PasswordResetView(FormView, CurrentAppMixin):
    """
    This is a class based version of django.contrib.auth.views.password_reset.
    The intention is to make the view easier to extend (in my case to use ajax)
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
    This is a class based version of django.contrib.auth.views.password_reset_confirm
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    The intention is to make the view easier to extend (in my case to use ajax)
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