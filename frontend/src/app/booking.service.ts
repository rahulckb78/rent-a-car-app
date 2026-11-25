import { Injectable, inject } from '@angular/core';
import { ApiService } from './core/api.service';
import { Booking, BookingRequest, Resource, ResourceDetail, Slot } from './models';

@Injectable({ providedIn: 'root' })
export class BookingService {
  private readonly api = inject(ApiService);

  resources = () => this.api.get<Resource[]>('/api/resources');
  resource = (id: string) => this.api.get<ResourceDetail>(`/api/resources/${encodeURIComponent(id)}`);
  availability = (id: string, date: string) =>
    this.api.get<Slot[]>(`/api/resources/${encodeURIComponent(id)}/availability?date=${date}`);
  create = (body: BookingRequest) => this.api.post<{ bookingId: number; total: number }>('/api/bookings', body);
  mine = () => this.api.get<Booking[]>('/api/bookings/mine');
  cancel = (id: number) => this.api.post<{ ok: boolean }>(`/api/bookings/${id}/cancel`);
}
