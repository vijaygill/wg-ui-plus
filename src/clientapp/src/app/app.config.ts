import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideClientHydration, withNoIncrementalHydration } from '@angular/platform-browser';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi, withXsrfConfiguration, withXhr } from '@angular/common/http';
import { HttpClientErrorInterceptor } from './http-client-error.interceptor';

import { routes } from './app.routes';


export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withXhr(), withXsrfConfiguration(
      {
        cookieName: 'csrftoken',
        headerName: 'X-CSRFToken',
      }
    )),
    provideAnimationsAsync(),
    provideRouter(routes), provideAnimationsAsync('noop'),
    provideClientHydration(withNoIncrementalHydration()), provideHttpClient(withXhr(), withInterceptorsFromDi()),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpClientErrorInterceptor,
      multi: true,
    },]
};
