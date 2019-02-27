import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing';
import {async, TestBed} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {MatButtonModule, MatCheckboxModule, MatGridListModule, MatIconModule, MatMenuModule} from '@angular/material';
import {MatCardModule} from '@angular/material/card';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatSelectModule} from '@angular/material/select';
import {MatTableModule} from '@angular/material/table';
import {MatTabsModule} from '@angular/material/tabs';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {OAuthService, UrlHelperService} from 'angular-oauth2-oidc';
import {environment} from '../environments/environment';
import {AppComponent} from './app.component';
import {MockOAuthService} from './google-auth.service';
import {JobComponent} from './job/job.component';
import {LogDisplayComponent} from './log-display/log-display.component';
import {PlanSideDisplayComponent} from './plan-side-display/plan-side-display.component';
import {PlanStatusCardComponent} from './plan-status-card/plan-status-card.component';
import {ProjectsComponent} from './projects/projects.component';
import {StageDetailsComponent} from './stage-details/stage-details.component';
import {StepDetailsComponent} from './step-details/step-details.component';
import {TimingDisplayComponent} from './timing-display/timing-display.component';
import {VisDisplayComponent} from './vis-display/vis-display.component';

describe('AppComponent', () => {
  beforeEach(async(() => {
    TestBed
        .configureTestingModule({
          imports: [
            RouterTestingModule,
            HttpClientTestingModule,
            FormsModule,
            BrowserAnimationsModule,
            MatButtonModule,
            MatCardModule,
            MatCheckboxModule,
            MatExpansionModule,
            MatFormFieldModule,
            MatGridListModule,
            MatIconModule,
            MatInputModule,
            MatMenuModule,
            MatPaginatorModule,
            MatSelectModule,
            MatTableModule,
            MatTabsModule,
          ],
          providers: [
            {provide: OAuthService, useClass: MockOAuthService},
            UrlHelperService,
          ],
          declarations: [
            AppComponent,
            JobComponent,
            LogDisplayComponent,
            ProjectsComponent,
            TimingDisplayComponent,
            VisDisplayComponent,
            PlanStatusCardComponent,
            PlanSideDisplayComponent,
            StageDetailsComponent,
            StepDetailsComponent,
          ]
        })
        .compileComponents();
  }));

  it('should run tests in the test environment', () => {
    expect(environment.name).toEqual('test');
  });

  it('should create the app', async(() => {
       const fixture = TestBed.createComponent(AppComponent);
       const app = fixture.debugElement.componentInstance;
       expect(app).toBeTruthy();
     }));

  it(`should have as title 'BQ Visualizer'`, async(() => {
       const fixture = TestBed.createComponent(AppComponent);
       const app = fixture.debugElement.componentInstance;
       expect(app.title).toEqual('BQ Visualizer');
     }));

  it('should render title in a h1 tag', async(() => {
       const fixture = TestBed.createComponent(AppComponent);
       fixture.detectChanges();
       const compiled = fixture.debugElement.nativeElement;
       expect(compiled.querySelector('h1').textContent)
           .toContain('BQ Visualizer');
     }));
});