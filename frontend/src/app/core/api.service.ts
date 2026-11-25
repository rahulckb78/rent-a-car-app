import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/** One place for HTTP: relative URLs (same origin), and server messages surfaced verbatim as Error.message. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  get<T>(url: string): Promise<T> {
    return this.send<T>('GET', url);
  }

  post<T>(url: string, body: unknown = {}): Promise<T> {
    return this.send<T>('POST', url, body);
  }

  private async send<T>(method: string, url: string, body?: unknown): Promise<T> {
    try {
      return await firstValueFrom(this.http.request<T>(method, url, { body }));
    } catch (err) {
      if (err instanceof HttpErrorResponse) {
        throw new Error(err.error?.error || (err.status === 0 ? 'Cannot reach the server' : `Request failed (${err.status})`));
      }
      throw err;
    }
  }
}
