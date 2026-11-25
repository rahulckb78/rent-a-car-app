import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiService } from './api.service';

export interface User {
  id: string;
  name: string;
  email: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  /** undefined = still asking the server, null = signed out. */
  readonly user = signal<User | null | undefined>(undefined);
  readonly ready = computed(() => this.user() !== undefined);

  /** Run once at startup (provideAppInitializer) so guards and the navbar never flash the wrong state. */
  async load(): Promise<void> {
    try {
      this.user.set((await this.api.get<{ user: User | null }>('/api/auth/me')).user);
    } catch {
      this.user.set(null);
    }
  }

  async signIn(email: string, password: string): Promise<void> {
    this.user.set((await this.api.post<{ user: User }>('/api/auth/sign-in', { email, password })).user);
  }

  async signUp(name: string, email: string, password: string): Promise<void> {
    this.user.set((await this.api.post<{ user: User }>('/api/auth/sign-up', { name, email, password })).user);
  }

  async signOut(): Promise<void> {
    await this.api.post('/api/auth/sign-out');
    this.user.set(null);
  }
}

/** Only follow in-app paths after sign-in ("/x", never "//evil.com" or "https://..."): open-redirect guard. */
export function safeReturnUrl(value: string | null | undefined): string {
  return value && value.startsWith('/') && !value.startsWith('//') && !value.includes('\\') ? value : '/';
}
