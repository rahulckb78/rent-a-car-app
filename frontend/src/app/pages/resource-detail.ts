import { Component, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { BookingService } from '../booking.service';
import { ResourceDetail, Slot } from '../models';

/** "YYYY-MM-DD" for the user's local calendar day. toISOString() would convert to UTC and can show the wrong day near midnight. */
const localToday = () => new Date().toLocaleDateString('en-CA');

@Component({
  selector: 'app-resource-detail',
  imports: [RouterLink],
  template: `
    @if (status() === 'loading') {
      <div class="page"></div>
    } @else if (status() === 'error' || !resource()) {
      <div class="page">
        <p class="empty-state">Car not found.</p>
        <a routerLink="/" class="btn btn-secondary">Back</a>
      </div>
    } @else {
      @let r = resource()!;
      <div class="page">
        <a routerLink="/" class="back-link">← Back</a>
        <div class="detail">
          <img [src]="r.image" [alt]="r.name" class="detail-image" />
          <div>
            <span class="category-tag">{{ r.category }}</span>
            <h1>{{ r.name }}</h1>
            <p class="card-meta">★ {{ r.rating.toFixed(1) }} · ₹{{ r.pricePerSlot.toFixed(0) }} per {{ r.slotMinutes }} min</p>
            <p>{{ r.description }}</p>

            <form class="booking-form" (submit)="book($event)">
              <label>
                Date
                <input type="date" [value]="date()" [min]="today" (change)="changeDate($any($event.target).value)" required />
              </label>

              <div>
                <span class="field-label">Time</span>
                @if (slotsLoading()) {
                  <p class="empty-state">Loading times...</p>
                } @else if (slots().length === 0) {
                  <p class="empty-state">No times for this day.</p>
                } @else {
                  <div class="slot-grid">
                    @for (s of slots(); track s.start) {
                      <button type="button" class="slot" [class.slot-selected]="selected() === s.start" [disabled]="!s.available" (click)="selected.set(s.start)">
                        {{ s.start }}
                      </button>
                    }
                  </div>
                }
              </div>

              <label>
                Duration
                <select [value]="count()" (change)="count.set(+$any($event.target).value)">
                  @for (n of counts(); track n) {
                    <option [value]="n" [selected]="n === count()">{{ n * r.slotMinutes }} min</option>
                  }
                </select>
              </label>
              <label>
                Name
                <input [value]="name()" (input)="nameInput.set($any($event.target).value)" required maxlength="100" />
              </label>
              <label>
                Notes (optional)
                <input [value]="notes()" maxlength="500" (input)="notes.set($any($event.target).value)" />
              </label>

              @if (selected() && !runValid()) {
                <p class="form-error">Not enough consecutive free time from {{ selected() }}.</p>
              }
              @if (error()) {
                <p class="form-error">{{ error() }}</p>
              }
              <button type="submit" class="btn btn-primary btn-wide" [disabled]="!selected() || !runValid() || submitting()">
                {{ submitting() ? 'Booking...' : auth.user() ? 'Book for ₹' + total().toFixed(0) : 'Sign in to book' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    }
  `,
})
export class ResourceDetailPage {
  /** Bound from the :id route param (withComponentInputBinding). */
  readonly id = input.required<string>();

  protected readonly auth = inject(AuthService);
  private readonly svc = inject(BookingService);
  private readonly router = inject(Router);

  protected readonly today = localToday();
  protected readonly resource = signal<ResourceDetail | null>(null);
  protected readonly status = signal<'loading' | 'ready' | 'error'>('loading');
  protected readonly date = signal(localToday());
  // Availability carries the request key it belongs to: "loading" is derived, and a late response for an
  // older date/refresh is ignored instead of overwriting newer data.
  private readonly availability = signal<{ key: string; slots: Slot[] }>({ key: '', slots: [] });
  private requestKey = '';
  private reloads = 0;
  protected readonly selected = signal<string | null>(null);
  protected readonly count = signal(1);
  protected readonly nameInput = signal<string | null>(null); // null = untouched, use the account name
  protected readonly notes = signal('');
  protected readonly error = signal('');
  protected readonly submitting = signal(false);

  protected readonly slots = computed(() => this.availability().slots);
  protected readonly slotsLoading = signal(true);
  protected readonly name = computed(() => this.nameInput() ?? this.auth.user()?.name ?? '');
  protected readonly counts = computed(() => Array.from({ length: this.resource()?.maxSlots ?? 1 }, (_, i) => i + 1));

  /** `count` consecutive free slots starting at the selected one must exist. */
  protected readonly runValid = computed(() => {
    const all = this.slots();
    const i = all.findIndex((s) => s.start === this.selected());
    const run = i === -1 ? [] : all.slice(i, i + this.count());
    return run.length === this.count() && run.every((s) => s.available);
  });
  protected readonly total = computed(() => (this.resource()?.pricePerSlot ?? 0) * this.count());

  ngOnInit() {
    this.svc
      .resource(this.id())
      .then((r) => {
        this.resource.set(r);
        this.status.set('ready');
      })
      .catch(() => this.status.set('error'));
    void this.loadAvailability();
  }

  protected changeDate(value: string) {
    this.date.set(value);
    this.selected.set(null);
    void this.loadAvailability();
  }

  private async loadAvailability() {
    const key = `${this.id()}|${this.date()}|${this.reloads++}`;
    this.requestKey = key;
    this.slotsLoading.set(true);
    let slots: Slot[] = [];
    try {
      slots = await this.svc.availability(this.id(), this.date());
    } catch {
      /* show "no times" */
    }
    if (this.requestKey !== key) return; // a newer request superseded this one
    this.availability.set({ key, slots });
    this.slotsLoading.set(false);
  }

  protected async book(event: Event) {
    event.preventDefault();
    if (!this.auth.user()) {
      await this.router.navigate(['/sign-in'], { queryParams: { returnUrl: `/resource/${this.id()}` } });
      return;
    }
    this.submitting.set(true);
    this.error.set('');
    try {
      await this.svc.create({
        resourceId: this.id(),
        date: this.date(),
        startTime: this.selected()!,
        slots: this.count(),
        name: this.name(),
        notes: this.notes(),
      });
      await this.router.navigateByUrl('/bookings');
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : 'Could not book');
      this.selected.set(null);
      void this.loadAvailability(); // the slot may have just been taken
    } finally {
      this.submitting.set(false);
    }
  }
}
