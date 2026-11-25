import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Client-side UX only. The API enforces auth for real (401). */
export const authGuard: CanActivateFn = (_route, state) => {
  const router = inject(Router);
  return inject(AuthService).user() ? true : router.createUrlTree(['/sign-in'], { queryParams: { returnUrl: state.url } });
};
