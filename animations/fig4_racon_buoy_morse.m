%% fig4_racon_buoy_morse.m  —  RACON working principle (JACON clinic)
%
% EVERY NUMBER BELOW IS TAKEN FROM A SPEC SHEET. Sources at the bottom.
%
% Radar (Furuno 18x4C/19x4C-BB series, the set we are testing against):
%   rotation            24 rpm nominal  (2.50 s per revolution)
%   horizontal beamwidth 5.2 deg        (2.2 kW radome, micro-strip)
%   sidelobes           -19 dB within +/-20 deg of the main lobe
%   pulse length / PRR  0.08 us / 2100 Hz   (0.125-1.5 nm scale)
%                       0.30 us / 1200 Hz   (1.5-3 nm)
%                       0.80 us /  600 Hz   (3-72 nm)
%   range scale shown   6 nm = 11.1 km
%
% Racon (USCG Navigation Center, "Radar Beacons"):
%   answers EVERY radar pulse it receives
%   begins replying   < 700 ns after interrogation
%   coded response    ~25 us of Morse; dash = 3 dots, dot = 1 space
%   paints on the display just BEYOND the structure's own echo
%
% Geometry this produces:
%   buoy at 2.0 nm = 3.70 km -> 12.4 us out, 24.7 us round trip
%   25 us of Morse -> 2.02 nm = 3.74 km of painted code (range = c*t/2)
%   so the code runs 3.70 -> 7.45 km
%   beam dwell on buoy = 5.2/360 * 2.5 s = 36 ms -> ~22 interrogations
%   per pass at 600 Hz PRR
%
% TWO TIME SCALES, and how they are handled here:
%   The antenna NEVER stops - it is a continuously rotating scanner. But
%   the whole interrogate-and-reply exchange lasts ~50 us, during which a
%   24 rpm antenna turns 0.0036 deg. It is therefore impossible to show
%   both on one clock. So this animation uses two:
%     ROTATION CLOCK - runs the sweep and the phosphor fade. Normal speed
%       is 6x slower than life; after the first pass it goes 3x faster so
%       the fade and the next refresh arrive quickly (marked on screen).
%     EXCHANGE CLOCK - during a pass, time zooms by ~10^5 so the ~50 us
%       exchange is watchable. The rotation clock is effectively stopped
%       for that window because in real time it has not moved (0.0036 deg).
%       This is a time zoom, NOT the antenna pausing.
%
% Colour key: RED = ship radar pulse, YELLOW = buoy struck,
%             GREEN = buoy keying / racon reply.
%
% Output: racon_buoy_morse.mp4
%
% Sources:
%   Furuno 18x4C-BB/19x4C-BB Operator's Manual, SPECIFICATIONS SP-1.
%   USCG Navigation Center, "Radar Beacons" (navcen.uscg.gov/radar-beacons).
%   radartutorial.eu, PPI-scope (long-persistence phosphor).

close all; clc;

%% ---- Theme ----
colBG  = [0 0 0];
colPhos= [0.30 1.00 0.40];
colSec = [0.10 0.65 0.28];
colRed = [1.00 0.25 0.20];
colYel = [1.00 0.85 0.10];
colIdle= [0.55 0.60 0.55];

%% ---- Spec-sheet parameters ----
c_ms = 299792458;                % m/s
nmi  = 1852;                     % m

rpm          = 24;
beamWidth3dB = 5.2;              % deg
R_buoy_nm    = 2.0;
R_max_nm     = 6.0;

code_us = 25;                            % USCG: ~25 us Morse response
unit_us = code_us/7;
markInt = [0 unit_us; 2*unit_us 5*unit_us; 6*unit_us 7*unit_us];   % dot dash dot

km          = 1/1000;
R_buoy      = R_buoy_nm*nmi*km;          % 3.704 km
R_max       = R_max_nm*nmi*km;           % 11.112 km
codeKm      = c_ms*(code_us*1e-6)/2*km;  % 3.747 km of painted code
R_codeEnd   = R_buoy + codeKm;           % 7.45 km
ringsKm     = [2 4 6 8 10];

xShip = 0.6;  xBuoy = 9.2;  y0 = 0;  laneY = 1.55;   % schematic, not to scale
thetaBuoy = deg2rad(62);

%% ---- Clocks ----
fps          = 20;
framesPerRev = 300;                           % 15 s of video per revolution
slowMo       = (framesPerRev/fps)/(60/rpm);   % 6x slower than life
sweepRate    = 2*pi/framesPerRev;
leadDeg      = 48;                            % 48/1.2 = 40 frames = 2.0 s to first pass
thetaStart   = thetaBuoy - deg2rad(leadDeg);
nFrames      = 345;

nOutF = 5; nBackF = 4;
codeLens  = [2 2 6 2 2];                      % dot gap dash gap dot, 1:1:3:1:1
codeStart = nOutF + nBackF;
codeEdges = codeStart + [0 cumsum(codeLens)];
nExchange = codeEdges(end);                   % frames per exchange (exchange clock)

leadFrames = deg2rad(leadDeg)/sweepRate;      % 40
tRotCross  = leadFrames + (0:5)*framesPerRev; % rotation-clock times of each pass
fastRate   = 3;
tRotFast   = leadFrames + 30;                 % fast-forward once past the first pass

tauPersist = 0.42*framesPerRev;
alphaFloor = 0.06;

speedBuoy = (xBuoy-xShip)/10;
shipHalfWidth=0.5; lambdaShip=0.22; ampShip=0.35;
lambdaBuoy=0.32;   ampBuoy=0.35;

outFile = fullfile(fileparts(mfilename('fullpath')), 'racon_buoy_morse.mp4');
v = VideoWriter(outFile,'MPEG-4'); v.FrameRate=fps; v.Quality=92; open(v);

fig = figure('Color',colBG,'Position',[40 25 1500 760]);

tRot = 0; inEx = false; eEx = 0; nCross = 0; tLastCross = NaN; painted = false;

for f = 1:nFrames

    % ---- enter an exchange when the beam reaches the buoy ----
    if ~inEx && nCross < numel(tRotCross) && tRot >= tRotCross(nCross+1)
        inEx = true; eEx = 0; nCross = nCross + 1;
        tLastCross = tRot; painted = true;
    end

    if inEx
        rate = 0;                                  % time-zoomed: 0.0036 deg of travel
    elseif tRot >= tRotFast
        rate = fastRate;
    else
        rate = 1;
    end

    sweepAngle = thetaStart + tRot*sweepRate;      % rotation clock only

    % ---- exchange state ----
    buoyCol = colIdle;  E_us = 0;  shipPulse = 0;  pulseFrac = 0;
    if inEx
        e = eEx;
        if e < nOutF
            shipPulse = 1; pulseFrac = e/max(nOutF-1,1);
        elseif e < codeStart
            buoyCol = colYel; shipPulse = 2; pulseFrac = (e-nOutF)/max(nBackF-1,1);
        else
            buoyCol = colPhos;
            k = find(e >= codeEdges(1:end-1) & e < codeEdges(2:end), 1);
            p = (e - codeEdges(k) + 1)/codeLens(k);
            cumU = [0 1 2 5 6];  stepU = [1 1 3 1 1];
            E_us = (cumU(k) + p*stepU(k))*unit_us;
        end
    elseif painted
        E_us = code_us;                            % code complete, now fading
    end

    % ---- phosphor persistence, on the rotation clock ----
    if painted, glow = max(alphaFloor, exp(-(tRot-tLastCross)/tauPersist)); else, glow = 0; end
    gPhos = colPhos*glow;  gRed = colRed*glow;  gBuoy = buoyCol*max(glow,0.35);

    clf(fig);

    % ========== Panel 1: physical wave propagation ==========
    ax1 = axes('Position',[0.02 0.63 0.96 0.34]); hold(ax1,'on');
    set(ax1,'Color',colBG);
    rectangle(ax1,'Position',[-0.5 -3 11 6],'FaceColor',colBG,'EdgeColor','none');
    drawShip(ax1, xShip, y0, colPhos, sweepAngle);
    drawBuoy(ax1, xBuoy, y0, buoyCol, colPhos);

    plot(ax1,[xShip xBuoy],[laneY laneY],'Color',colSec,'LineWidth',1);
    plot(ax1,[xShip xShip],[0.85 laneY],':','Color',colSec);
    plot(ax1,[xBuoy xBuoy],[0.85 laneY],':','Color',colSec);

    if shipPulse == 1
        cx = xShip + pulseFrac*(xBuoy-xShip);
        [xs,ys] = rigidPacket(cx, shipHalfWidth, lambdaShip, ampShip);
        plot(ax1, xs, laneY+ys, 'Color', colRed, 'LineWidth',1.8);
    elseif shipPulse == 2
        cx = xBuoy - pulseFrac*(xBuoy-xShip);
        [xs,ys] = rigidPacket(cx, shipHalfWidth, lambdaShip, ampShip*0.7);
        plot(ax1, xs, laneY+ys, 'Color', colRed, 'LineWidth',1.8);
    end
    if inEx
        for m = [1 3 5]
            [xL,xT,act] = packetEdges(eEx,codeEdges(m),codeEdges(m+1)-1,speedBuoy,xBuoy,xShip);
            if act
                [xs,ys] = growPacket(xL,xT,lambdaBuoy,ampBuoy);
                plot(ax1,xs,laneY+ys,'Color',colPhos,'LineWidth',1.8);
            end
        end
    end
    axis(ax1,[-0.5 10.5 -1.6 2.1]); axis(ax1,'equal'); axis(ax1,'off');
    title(ax1,sprintf('Ship & RACON buoy — %.2f km apart',R_buoy), ...
        'Color',colPhos,'FontWeight','normal','FontSize',12);

    % ========== Panel 2: PPI ==========
    axp = axes('Position',[0.05 0.055 0.36 0.53]); hold(axp,'on'); axis(axp,'equal');
    set(axp,'Color',colBG);
    th = linspace(0,2*pi,140);
    for rr = ringsKm/R_max
        plot(axp, rr*cos(th), rr*sin(th), 'Color', colSec, 'LineWidth',1);
    end
    for rr = ringsKm
        text(axp, 0, rr/R_max+0.045, sprintf('%g',rr), 'Color', colSec, ...
            'FontSize',7,'HorizontalAlignment','center');
    end

    [lx,ly] = beamPattern(sweepAngle, beamWidth3dB, 25);
    patch(axp, lx, ly, colPhos, 'FaceAlpha',0.40, 'EdgeColor',colPhos, ...
        'LineWidth',0.75, 'EdgeAlpha',0.9);
    plot(axp,0,0,'^','MarkerSize',9,'MarkerFaceColor',colPhos,'MarkerEdgeColor',colPhos);

    if painted
        for k=1:size(markInt,1)
            a = markInt(k,1); b = min(markInt(k,2),E_us);
            if b > a
                ra = (R_buoy + (a/code_us)*codeKm)/R_max;
                rb = (R_buoy + (b/code_us)*codeKm)/R_max;
                plot(axp,[ra rb]*cos(thetaBuoy),[ra rb]*sin(thetaBuoy), ...
                    '-','Color',gPhos,'LineWidth',6);
            end
        end
        rB = R_buoy/R_max;
        plot(axp,rB*cos(thetaBuoy),rB*sin(thetaBuoy),'o','MarkerSize',10, ...
            'MarkerFaceColor',gBuoy,'MarkerEdgeColor',gBuoy);
    end
    axis(axp,[-1.15 1.15 -1.15 1.15]); axis(axp,'off');
    title(axp,sprintf('PPI — %d rpm, %.1f° beam, %.1f km scale',rpm,beamWidth3dB,R_max), ...
        'Color',colPhos,'FontWeight','normal','FontSize',11);

    % ========== Panel 3: Radar scope ==========
    ax2 = axes('Position',[0.48 0.055 0.48 0.53]); hold(ax2,'on'); box(ax2,'off');
    set(ax2,'Color',colBG,'XColor',colPhos,'YColor',colPhos);
    xlim(ax2,[0 R_max]); ylim(ax2,[0 1.3]);
    grid(ax2,'on'); ax2.GridColor = colSec; ax2.GridAlpha = 0.45;
    set(ax2,'XTick',0:2:10,'YTick',[]);
    plot(ax2,[0 0],[0 1],'Color',colRed,'LineWidth',3);          % TX, every PRI
    if painted && (~inEx || eEx >= codeStart)
        plot(ax2,[R_buoy R_buoy],[0 1],'Color',gRed,'LineWidth',3);
    end
    if painted
        for k=1:size(markInt,1)
            a = markInt(k,1); b = min(markInt(k,2),E_us);
            if b > a
                plot(ax2,[R_buoy+(a/code_us)*codeKm, R_buoy+(b/code_us)*codeKm], ...
                    [0.55 0.55],'-','Color',gPhos,'LineWidth',9);
            end
        end
        % floating scale: time since the buoy keyed up, just two numbers
        yr = 0.36;
        plot(ax2,[R_buoy R_codeEnd],[yr yr],'-','Color',gPhos,'LineWidth',1);
        plot(ax2,[R_buoy R_buoy],[yr-0.045 yr+0.045],'-','Color',gPhos,'LineWidth',1);
        plot(ax2,[R_codeEnd R_codeEnd],[yr-0.045 yr+0.045],'-','Color',gPhos,'LineWidth',1);
        text(ax2,R_buoy+0.22,yr-0.135,'0','Color',gPhos,'FontSize',8,'HorizontalAlignment','center');
        text(ax2,R_codeEnd,yr-0.135,sprintf('%g µs',code_us),'Color',gPhos, ...
            'FontSize',8,'HorizontalAlignment','center');
        if E_us >= code_us - 1e-9
            text(ax2,(R_buoy+R_codeEnd)/2,0.80,'.  —  .   =   R','Color',gPhos, ...
                'FontSize',11,'FontWeight','bold','HorizontalAlignment','center');
        end
    end
    xlabel(ax2,'Range [km]','Color',colPhos);
    % panel label sits inside the trace; the top edge belongs to the time axis
    text(ax2,0.28,1.19,'Radar scope','Color',colPhos,'FontSize',12,'VerticalAlignment','middle');

    % second x-axis: time since the ship transmitted (range = c t / 2)
    tTicksUs = [0 20 40 60];
    tTicksKm = c_ms*(tTicksUs*1e-6)/2*km;
    ax2t = axes('Position',get(ax2,'Position'),'Color','none', ...
        'XAxisLocation','top','YAxisLocation','right', ...
        'XColor',colPhos,'YColor','none','Box','off');
    set(ax2t,'XLim',[0 R_max],'YLim',[0 1.3],'YTick',[], ...
        'XTick',tTicksKm,'XTickLabel',compose('%d',tTicksUs));
    xlabel(ax2t,'Time since ship transmitted [µs]','Color',colPhos);

    % ---- playback / time-zoom marker ----
    if inEx
        annotation(fig,'textbox',[0.700 0.942 0.285 0.052], ...
            'String',sprintf('time zoom  —  %g µs exchange',code_us+25), ...
            'FontWeight','bold','FontSize',14,'Color',colYel,'EdgeColor','none', ...
            'HorizontalAlignment','right','VerticalAlignment','middle');
    elseif rate > 1
        annotation(fig,'textbox',[0.745 0.942 0.240 0.052], ...
            'String',sprintf('>>  %dx playback',rate), ...
            'Interpreter','none','FontWeight','bold','FontSize',15, ...
            'Color',colYel,'EdgeColor','none', ...
            'HorizontalAlignment','right','VerticalAlignment','middle');
    end

    drawnow;
    writeVideo(v, getframe(fig));

    % ---- advance whichever clock is running ----
    if inEx
        eEx = eEx + 1;
        if eEx >= nExchange, inEx = false; end
    else
        tRot = tRot + rate;
    end
end

close(v);
fprintf(['Wrote %s\n  %d frames, %.1f s video\n  %d rpm shown %.1fx slow, then %dx faster\n' ...
         '  passes: %d;  buoy %.2f km;  code %.0f us = %.2f km (%.2f-%.2f km)\n'], ...
    outFile, nFrames, nFrames/fps, rpm, slowMo, fastRate, nCross, R_buoy, ...
    code_us, codeKm, R_buoy, R_codeEnd);

%% ---- local helpers ----
function [xs,ys] = beamPattern(aC, bw3dBdeg, spanDeg)
    DoverLambda = 0.886/deg2rad(bw3dBdeg);
    th = linspace(-deg2rad(spanDeg), deg2rad(spanDeg), 361);
    u  = pi*DoverLambda*sin(th);
    g  = abs(sin(u)./u);  g(abs(u) < 1e-9) = 1;
    xs = [0, g.*cos(aC+th), 0];
    ys = [0, g.*sin(aC+th), 0];
end

function drawShip(ax,x,y,edgeCol,sweepAngle)
    hull = [-0.55 0.05; -0.50 0.26; -0.10 0.32; 0.25 0.30; 0.55 0.08; 0.30 -0.12; -0.30 -0.15];
    patch(ax, x+hull(:,1), y+hull(:,2), [0.04 0.04 0.04], 'EdgeColor', edgeCol, 'LineWidth', 1.5);
    patch(ax, x+[-0.16 -0.16 0.10 0.10], y+[0.30 0.55 0.55 0.30], [0.04 0.04 0.04], 'EdgeColor', edgeCol, 'LineWidth', 1.2);
    plot(ax, x+[-0.03 -0.03], y+[0.55 0.85], '-', 'Color', edgeCol, 'LineWidth', 1.5);
    r = 0.17;
    plot(ax, x-0.03+r*[-cos(sweepAngle) cos(sweepAngle)], y+0.85+0.45*r*[-sin(sweepAngle) sin(sweepAngle)], ...
        '-', 'Color', edgeCol, 'LineWidth', 2.2);
end

function drawBuoy(ax,x,y,fillCol,edgeCol)
    rectangle(ax,'Position',[x-0.25 y-0.5 0.5 0.5],'Curvature',0.25,'FaceColor',fillCol,'EdgeColor',edgeCol,'LineWidth',1.5);
    patch(ax,[x-0.22 x+0.22 x],[y+0.0 y+0.0 y+0.28], fillCol,'EdgeColor',edgeCol,'LineWidth',1.5);
    plot(ax,[x x],[y+0.28 y+0.65],'-','Color',edgeCol,'LineWidth',1.5);
    plot(ax, x, y+0.65, 'o', 'MarkerSize',4,'MarkerFaceColor',edgeCol,'MarkerEdgeColor',edgeCol);
    for ang = [45 135 225 315]
        drawHorn(ax, x, y+0.65, ang, 0.26, edgeCol);
    end
end

function drawHorn(ax,cx,cy,angleDeg,len,edgeCol)
    a = deg2rad(angleDeg);
    dirv = [cos(a) sin(a)]; perp = [-sin(a) cos(a)];
    baseW = 0.04; tipW = 0.16;
    p1 = [cx,cy] + perp*baseW/2;   p2 = [cx,cy] - perp*baseW/2;
    tip= [cx,cy] + dirv*len;
    p3 = tip + perp*tipW/2;        p4 = tip - perp*tipW/2;
    patch(ax,[p1(1) p3(1) p4(1) p2(1)],[p1(2) p3(2) p4(2) p2(2)], [0.04 0.04 0.04],'EdgeColor',edgeCol,'LineWidth',1.2);
end

function [xs,ys] = rigidPacket(centerX, halfWidth, lambda, amp)
    N  = max(30, round(2*halfWidth/lambda*24));
    xs = linspace(centerX-halfWidth, centerX+halfWidth, N);
    env= sin(pi*(xs-(centerX-halfWidth))/(2*halfWidth)).^2;
    ys = amp*env.*sin(2*pi*xs/lambda);
end

function [xs,ys] = growPacket(xLead, xTrail, lambda, amp)
    L = xTrail - xLead;
    if L <= 1e-6, xs=[]; ys=[]; return; end
    N = max(20, round(L/lambda*24));
    xs = linspace(xLead, xTrail, N);
    w  = min(0.22, L/2);
    env = ones(size(xs));
    frontMask = (xs-xLead) < w;
    env(frontMask) = 0.5*(1-cos(pi*(xs(frontMask)-xLead)/max(w,1e-6)));
    backMask = (xTrail-xs) < w;
    envBack  = 0.5*(1-cos(pi*(xTrail-xs(backMask))/max(w,1e-6)));
    env(backMask) = min(env(backMask), envBack);
    ys = amp*env.*sin(2*pi*xs/lambda);
end

function [xLead,xTrail,active] = packetEdges(t,onStart,onEnd,speed,xBuoy,xShip)
    if t < onStart
        xLead=xBuoy; xTrail=xBuoy; active=false; return;
    end
    elapsedOn = min(t,onEnd) - onStart + 1;
    leadDist  = elapsedOn*speed;
    if t <= onEnd, trailDist = 0; else, trailDist = (t-onEnd)*speed; end
    xLead  = max(xShip, xBuoy-leadDist);
    xTrail = max(xShip, xBuoy-trailDist);
    active = xTrail > xLead + 1e-6;
end
