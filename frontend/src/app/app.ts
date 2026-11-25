import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="navbar">
      <div class="navbar-inner">
        <a routerLink="/" class="brand">RentACar</a>
        <nav class="nav-links">
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Cars</a>
          <a routerLink="/bookings" routerLinkActive="active">My rentals</a>
          @if (auth.user(); as user) {
            <span class="nav-user">{{ user.name || user.email }}</span>
            <button class="btn btn-small btn-secondary" (click)="signOut()">Sign out</button>
          } @else {
            <a routerLink="/sign-in" class="btn btn-small btn-secondary">Sign in</a>
          }
        </nav>
      </div>
    </header>
    <main><router-outlet /></main>
  `,
})
export class App {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected async signOut() {
    await this.auth.signOut();
    await this.router.navigateByUrl('/');
  }
}
