import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, catchError, tap, throwError } from 'rxjs';
import { WebapiService } from './webapi.service';
import { ServerStatus } from './webapi.entities';

@Injectable({
  providedIn: 'root',
})
export class HttpClientErrorInterceptor implements HttpInterceptor {

  constructor(private webapiService: WebapiService) { }

  private httpErrors: { [status: number]: string } = {
    0: 'Error while communicating with server.',
    400: 'Bad request. Probably invalid data.',
    401: 'Unauthorised call to server.',
    403: 'Client is forbidden from calling server.',
    404: 'Client is forbidden from calling server.',
    500: 'Internal Server Error.',
  }

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(request)
      .pipe(
        catchError((error: HttpErrorResponse) => {
          let m = error.error && error.error.message ? error.error.message : '';
          let message = 'Server returned HTTP Error '
            + error.status
            + '. '
            + (m ? m + '. ' : '')
            + (error.status in this.httpErrors ? this.httpErrors[error.status] : 'Please check logs on server side.');

          this.webapiService.pushServerStatus({ status: 'error', message: message } as ServerStatus)
          return throwError(() => new Error(message));
        })
      );
  }
}
