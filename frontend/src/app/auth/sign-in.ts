import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService, safeReturnUrl } from '../core/auth.service';

@Component({
  selector: 'app-sign-in',
  imports: [RouterLink],
  template: `
    <div class="page auth-page">
      <h1>Sign in</h1>
      <form class="auth-form" (submit)="submit($event, email.value, password.value)">
        <label>Email <input #email type="email" name="email" required autocomplete="email" /></label>
        <label>Password <input #password type="password" name="password" required autocomplete="current-password" /></label>
        @if (error()) {
          <p class="form-error">{{ error() }}</p>
        }
        <button type="submit" class="btn btn-primary btn-wide" [disabled]="submitting()">
          {{ submitting() ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
      <p class="auth-switch">
        New here? <a routerLink="/sign-up" [queryParams]="route.snapshot.queryParams">Create an account</a>
      </p>
    </div>
  `,
})
export class SignIn {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  protected readonly route = inject(ActivatedRoute);
  protected readonly error = signal('');
  protected readonly submitting = signal(false);

  protected async submit(event: Event, email: string, password: string) {
    event.preventDefault();
    this.submitting.set(true);
    this.error.set('');
    try {
      await this.auth.signIn(email, password);
      await this.router.navigateByUrl(safeReturnUrl(this.route.snapshot.queryParamMap.get('returnUrl')), { replaceUrl: true });
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : 'Could not sign in');
    } finally {
      this.submitting.set(false);
    }
  }
}
