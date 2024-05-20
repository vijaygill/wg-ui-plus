import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { HttpClientModule, HttpClientXsrfModule, provideHttpClient } from '@angular/common/http';

export const appConfig: ApplicationConfig = {

  providers: [importProvidersFrom(HttpClientModule),
    provideRouter(routes), provideClientHydration(), provideHttpClient(),
    importProvidersFrom(
      HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'csrftoken',
    })
  ),]
};
