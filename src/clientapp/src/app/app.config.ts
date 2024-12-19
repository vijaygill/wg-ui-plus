import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideClientHydration } from '@angular/platform-browser';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi, withXsrfConfiguration } from '@angular/common/http';
import { HttpClientErrorInterceptor } from './http-client-error.interceptor';

import { routes } from './app.routes';

import { providePrimeNG } from 'primeng/config';
import Aura from '@primeng/themes/aura';
import Lara from '@primeng/themes/lara';
import Meterial from '@primeng/themes/material';
import Nora from '@primeng/themes/nora';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withXsrfConfiguration(
      {
        cookieName: 'csrftoken',
        headerName: 'X-CSRFToken',
      }
    )),
    provideAnimationsAsync(),
    providePrimeNG({
      theme: {
        preset: Lara,
        options: {
          darkModeSelector: '.my-app-dark',
        }
      }
    }),
    provideRouter(routes), provideAnimationsAsync('noop'),
    provideClientHydration(), provideHttpClient(withInterceptorsFromDi()),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpClientErrorInterceptor,
      multi: true,
    },]
};
