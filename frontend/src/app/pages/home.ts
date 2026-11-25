import { Component, computed, inject, signal } from '@angular/core';
import { BookingService } from '../booking.service';
import { ResourceCard } from '../components/resource-card';
import { Resource } from '../models';

@Component({
  selector: 'app-home',
  imports: [ResourceCard],
  template: `
    <div class="page">
      <div class="hero">
        <h1>RentACar</h1>
        <p>Pick a car and drive away in minutes.</p>
      </div>

      <div class="toolbar">
        <input type="text" placeholder="Search cars..." [value]="search()" (input)="search.set($any($event.target).value)" />
        <div class="pills">
          @for (c of categories(); track c) {
            <button class="pill" [class.pill-active]="category() === c" (click)="category.set(c)">{{ c }}</button>
          }
        </div>
      </div>

      @switch (status()) {
        @case ('loading') { <p class="empty-state">Loading...</p> }
        @case ('error') { <p class="empty-state">Couldn't load cars. Is the server running?</p> }
        @default {
          @if (filtered().length === 0) {
            <p class="empty-state">No cars match your search.</p>
          } @else {
            <div class="grid">
              @for (r of filtered(); track r.id) {
                <app-resource-card [resource]="r" />
              }
            </div>
          }
        }
      }
    </div>
  `,
})
export class Home {
  private readonly svc = inject(BookingService);
  protected readonly resources = signal<Resource[]>([]);
  protected readonly status = signal<'loading' | 'ready' | 'error'>('loading');
  protected readonly category = signal('All');
  protected readonly search = signal('');

  protected readonly categories = computed(() => ['All', ...new Set(this.resources().map((r) => r.category))]);
  protected readonly filtered = computed(() => {
    const q = this.search().trim().toLowerCase();
    return this.resources().filter(
      (r) => (this.category() === 'All' || r.category === this.category()) && r.name.toLowerCase().includes(q),
    );
  });

  constructor() {
    this.svc
      .resources()
      .then((data) => {
        this.resources.set(data);
        this.status.set('ready');
      })
      .catch(() => this.status.set('error'));
  }
}
