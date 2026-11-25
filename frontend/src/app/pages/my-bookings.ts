import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BookingService } from '../booking.service';
import { Booking } from '../models';

@Component({
  selector: 'app-my-bookings',
  imports: [RouterLink],
  template: `
    <div class="page">
      <h1>My rentals</h1>
      @if (error()) {
        <p class="form-error">{{ error() }}</p>
      }
      @switch (status()) {
        @case ('loading') { <p class="empty-state">Loading...</p> }
        @case ('error') { <p class="empty-state">Couldn't load your rentals.</p> }
        @default {
          @if (bookings().length === 0) {
            <p class="empty-state">Nothing booked yet. <a routerLink="/">Browse cars</a></p>
          }
        }
      }
      <ul class="booking-list">
        @for (b of bookings(); track b.id) {
          <li class="booking" [class.booking-cancelled]="b.status === 'cancelled'">
            <div>
              <strong>{{ b.resourceName }}</strong>
              <div class="card-meta">{{ b.date }} · {{ b.startTime }}–{{ b.endTime }} · ₹{{ b.total.toFixed(0) }}</div>
              @if (b.notes) {
                <div class="card-meta">{{ b.notes }}</div>
              }
            </div>
            @if (b.status === 'confirmed') {
              <button class="btn btn-small btn-secondary" (click)="cancel(b.id)">Cancel</button>
            } @else {
              <span class="category-tag">Cancelled</span>
            }
          </li>
        }
      </ul>
    </div>
  `,
})
export class MyBookings {
  private readonly svc = inject(BookingService);
  protected readonly bookings = signal<Booking[]>([]);
  protected readonly status = signal<'loading' | 'ready' | 'error'>('loading');
  protected readonly error = signal('');

  constructor() {
    void this.load();
  }

  private async load() {
    try {
      this.bookings.set(await this.svc.mine());
      this.status.set('ready');
    } catch {
      this.status.set('error');
    }
  }

  protected async cancel(id: number) {
    if (!confirm('Cancel this rental?')) return;
    this.error.set('');
    try {
      await this.svc.cancel(id);
      await this.load();
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : 'Could not cancel');
    }
  }
}
