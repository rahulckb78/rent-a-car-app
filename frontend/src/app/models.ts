export interface Resource {
  id: string;
  name: string;
  category: string;
  pricePerSlot: number;
  rating: number;
  image: string;
  description: string;
  capacity: number;
}

export interface ResourceDetail extends Resource {
  slotMinutes: number;
  openHour: number;
  closeHour: number;
  maxSlots: number;
  maxDaysAhead: number;
}

export interface Slot {
  start: string;
  end: string;
  available: boolean;
}

export interface Booking {
  id: number;
  resourceId: string;
  resourceName: string;
  date: string;
  startTime: string;
  endTime: string;
  notes: string;
  total: number;
  status: 'confirmed' | 'cancelled';
  createdAt: string;
}

export interface BookingRequest {
  resourceId: string;
  date: string;
  startTime: string;
  slots: number;
  name: string;
  notes: string;
}
