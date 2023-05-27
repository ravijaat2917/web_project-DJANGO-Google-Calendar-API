# views.py
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from django.urls import reverse


class GoogleCalendarInitView(APIView):
    def get(self, request):
        flow = Flow.from_client_secrets_file(
            settings.GOOGLE_CLIENT_SECRET_FILE,
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            redirect_uri=request.build_absolute_uri(reverse('google-calendar-redirect'))
        )
        authorization_url, state = flow.authorization_url(access_type='offline')
        request.session['google_auth_state'] = state
        return redirect(authorization_url)


class GoogleCalendarRedirectView(APIView):
    def get(self, request):
        state = request.session.get('google_auth_state')
        flow = Flow.from_client_secrets_file(
            settings.GOOGLE_CLIENT_SECRET_FILE,
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            state=state,
            redirect_uri=request.build_absolute_uri(reverse('google-calendar-redirect'))
        )
        flow.fetch_token(authorization_response=request.build_absolute_uri(),
                         access_type='offline')

        credentials = flow.credentials
        request.session['google_credentials'] = credentials.to_json()
        return redirect(reverse('get-events'))


class GoogleCalendarEventsView(APIView):
    def get(self, request):
        credentials_json = request.session.get('google_credentials')
        if not credentials_json:
            return JsonResponse({'error': 'Google credentials not found.'}, status=400)

        credentials = google.auth.credentials.Credentials.from_json(credentials_json)
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

        service = build('calendar', 'v3', credentials=credentials)
        events_result = service.events().list(calendarId='primary', maxResults=10).execute()
        events = events_result.get('items', [])
        return JsonResponse({'events': events})
