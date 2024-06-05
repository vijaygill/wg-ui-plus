import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, catchError, tap, throwError } from 'rxjs';
import { ConfirmationDialogService } from './confirmation-dialog-service';
import { MessageService } from 'primeng/api';
import { WebapiService } from './webapi.service';
import { ServerStatus } from './webapi.entities';

@Injectable({
  providedIn: 'root',
})
export class HttpClientErrorInterceptor implements HttpInterceptor {

  constructor(private webapiService: WebapiService) { }

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(request)
      .pipe(
        catchError((error: HttpErrorResponse) => {
          if (error.status <= 0) {
            this.webapiService.pushServerStatus({ status: 'error', message: 'Error while communicating with server.' } as ServerStatus)
          }
          return throwError(error);
        })
      );
  }
}
