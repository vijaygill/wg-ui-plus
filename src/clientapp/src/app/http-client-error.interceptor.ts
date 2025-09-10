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

  private httpErrors: httpError[] = [
    { from: 0, to: 0, message: 'Error while communicating with server.' ,},
    { from: 401, to: 401, message: 'Unauthorised call to server.' ,},
    { from: 403, to: 403, message: 'Client is forbidden from calling server.' ,},
    { from: 404, to: 404, message: 'Resource not found.',},
    { from: 407, to: 407, message: 'Proxy Authentication Required.', },
    { from: 408, to: 408, message: 'Request Timeout.',},
    { from: 500, to: 500, message: 'Internal Server Error.'},
    { from: 501, to: 501, message: 'Not Implemented.'},
    { from: 502, to: 502, message: 'Bad Gateway. Possibly the reverse proxy cannot see upstream server.'},
    { from: 503, to: 599, message: 'Other error.'},
  ];

  getHttpError(statusCode: number): string | null {
    let x = this.httpErrors.find(item => item.from <= statusCode && statusCode <= item.to);
    let res = x ? x.message : null;
    return res;
  }

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(request)
      .pipe(
        catchError((error: HttpErrorResponse) => {
          let errorMessageFromList = this.getHttpError(error.status);
          if(!errorMessageFromList)
          {
            return throwError(() => error);  
          }
          let m = error.error && error.error.message ? error.error.message : '';
          let message = 'Server returned HTTP Error '
            + error.status
            + '. '
            + (m ? m + '. ' : '')
            + (errorMessageFromList ? errorMessageFromList : 'Please check logs on server side.');

          this.webapiService.pushServerStatus({ status: 'error', message: message } as ServerStatus)
          return throwError(() => new Error(message));
        })
      );
  }
}

interface httpError {
  from: number,
  to: number,
  message: string
}
