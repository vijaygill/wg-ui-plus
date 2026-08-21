import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideClientHydration, withNoIncrementalHydration } from '@angular/platform-browser';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi, withXsrfConfiguration, withXhr } from '@angular/common/http';
import { HttpClientErrorInterceptor } from './http-client-error.interceptor';

import { routes } from './app.routes';


export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideHttpClient(withXhr(), withXsrfConfiguration(
      {
        cookieName: 'csrftoken',
        headerName: 'X-CSRFToken',
      }
    ), withInterceptorsFromDi()),
    provideAnimationsAsync(),
    provideRouter(routes),
    provideClientHydration(withNoIncrementalHydration()),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpClientErrorInterceptor,
      multi: true,
    },
  ]
};
