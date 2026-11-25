import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Resource } from '../models';

@Component({
  selector: 'app-resource-card',
  imports: [RouterLink],
  template: `
    <a [routerLink]="['/resource', resource().id]" class="card">
      <img [src]="resource().image" [alt]="resource().name" loading="lazy" />
      <div class="card-body">
        <span class="category-tag">{{ resource().category }}</span>
        <h2>{{ resource().name }}</h2>
        <p class="card-meta">★ {{ resource().rating.toFixed(1) }} · ₹{{ resource().pricePerSlot.toFixed(0) }} / hour</p>
      </div>
    </a>
  `,
})
export class ResourceCard {
  readonly resource = input.required<Resource>();
}
