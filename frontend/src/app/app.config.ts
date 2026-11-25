import { provideHttpClient, withFetch } from '@angular/common/http';
import { ApplicationConfig, inject, provideAppInitializer, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { routes } from './app.routes';
import { AuthService } from './core/auth.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withFetch()),
    // Route params arrive as @Input / input() signals (e.g. :id -> id).
    provideRouter(routes, withComponentInputBinding()),
    // Ask the server who is signed in before the first render.
    provideAppInitializer(() => inject(AuthService).load()),
  ],
};
