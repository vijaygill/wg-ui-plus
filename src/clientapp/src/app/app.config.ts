import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideClientHydration } from '@angular/platform-browser';
import { HTTP_INTERCEPTORS, HttpClientModule, HttpClientXsrfModule, provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';
import { HttpClientErrorInterceptor } from './http-client-error.interceptor';

export const appConfig: ApplicationConfig = {

  providers: [importProvidersFrom(HttpClientModule),
  provideRouter(routes), provideAnimationsAsync('noop'),
  provideClientHydration(), provideHttpClient(withInterceptorsFromDi()),
  {
    provide: HTTP_INTERCEPTORS,
    useClass: HttpClientErrorInterceptor,
    multi: true,
  },
  importProvidersFrom(
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'X-CSRFToken',
    })
  ),]
};
