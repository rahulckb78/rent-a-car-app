import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService, safeReturnUrl } from '../core/auth.service';

@Component({
  selector: 'app-sign-up',
  imports: [RouterLink],
  template: `
    <div class="page auth-page">
      <h1>Create an account</h1>
      <form class="auth-form" (submit)="submit($event, name.value, email.value, password.value)">
        <label>Full name <input #name name="name" required autocomplete="name" maxlength="100" /></label>
        <label>Email <input #email type="email" name="email" required autocomplete="email" /></label>
        <label>
          Password
          <input #password type="password" name="password" required minlength="8" maxlength="128" autocomplete="new-password" />
        </label>
        @if (error()) {
          <p class="form-error">{{ error() }}</p>
        }
        <button type="submit" class="btn btn-primary btn-wide" [disabled]="submitting()">
          {{ submitting() ? 'Creating account...' : 'Sign up' }}
        </button>
      </form>
      <p class="auth-switch">
        Already have an account? <a routerLink="/sign-in" [queryParams]="route.snapshot.queryParams">Sign in</a>
      </p>
    </div>
  `,
})
export class SignUp {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  protected readonly route = inject(ActivatedRoute);
  protected readonly error = signal('');
  protected readonly submitting = signal(false);

  protected async submit(event: Event, name: string, email: string, password: string) {
    event.preventDefault();
    this.submitting.set(true);
    this.error.set('');
    try {
      await this.auth.signUp(name, email, password);
      await this.router.navigateByUrl(safeReturnUrl(this.route.snapshot.queryParamMap.get('returnUrl')), { replaceUrl: true });
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : 'Could not create account');
    } finally {
      this.submitting.set(false);
    }
  }
}
