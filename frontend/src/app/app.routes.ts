import { Routes } from '@angular/router';
import { SignIn } from './auth/sign-in';
import { SignUp } from './auth/sign-up';
import { authGuard } from './core/auth.guard';
import { Home } from './pages/home';
import { MyBookings } from './pages/my-bookings';
import { NotFound } from './pages/not-found';
import { ResourceDetailPage } from './pages/resource-detail';

export const routes: Routes = [
  { path: '', component: Home, title: 'RentACar' },
  { path: 'resource/:id', component: ResourceDetailPage, title: 'Car · RentACar' },
  { path: 'bookings', component: MyBookings, canActivate: [authGuard], title: 'My rentals · RentACar' },
  { path: 'sign-in', component: SignIn, title: 'Sign in · RentACar' },
  { path: 'sign-up', component: SignUp, title: 'Sign up · RentACar' },
  { path: '**', component: NotFound, title: 'Not found · RentACar' },
];
