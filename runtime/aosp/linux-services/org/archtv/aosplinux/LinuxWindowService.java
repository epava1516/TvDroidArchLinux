package org.archtv.aosplinux;

// Generated from the complete original IWindowManager contract.
public final class LinuxWindowService extends LocalServiceBinder implements android.view.IWindowManager {
    private final WindowPolicyState policy;
    public LinuxWindowService(java.nio.file.Path path) throws java.io.IOException {
        super("android.view.IWindowManager");policy=new WindowPolicyState(path);
    }
    private WindowPolicyState.Snapshot state(int display) throws android.os.DeadObjectException {
        if (!isBinderAlive()) throw new android.os.DeadObjectException();
        if (display!=0) throw new IllegalArgumentException("Only the app virtual display 0 is supported");
        try { return policy.read(); } catch (java.io.IOException failure) {
            try { close(); } catch (RuntimeException callback) { failure.addSuppressed(callback); }
            android.os.DeadObjectException dead=new android.os.DeadObjectException();dead.initCause(failure);throw dead;
        }
    }
    @Override public boolean startViewServer(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: startViewServer");
    }
    @Override public boolean stopViewServer() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: stopViewServer");
    }
    @Override public boolean isViewServerRunning() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isViewServerRunning");
    }
    @Override public android.view.IWindowSession openSession(android.view.IWindowSessionCallback p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: openSession");
    }
    @Override public boolean useBLAST() throws android.os.RemoteException {
        return state(0).blast;
    }
    @Override public void getInitialDisplaySize(int p0, android.graphics.Point p1) throws android.os.RemoteException {
        WindowPolicyState.Snapshot s=state(p0);java.util.Objects.requireNonNull(p1);p1.x=s.initialWidth;p1.y=s.initialHeight;
    }
    @Override public void getBaseDisplaySize(int p0, android.graphics.Point p1) throws android.os.RemoteException {
        WindowPolicyState.Snapshot s=state(p0);java.util.Objects.requireNonNull(p1);p1.x=s.width;p1.y=s.height;
    }
    @Override public void setForcedDisplaySize(int p0, int p1, int p2) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setForcedDisplaySize");
    }
    @Override public void clearForcedDisplaySize(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: clearForcedDisplaySize");
    }
    @Override public int getInitialDisplayDensity(int p0) throws android.os.RemoteException {
        return state(p0).density;
    }
    @Override public int getBaseDisplayDensity(int p0) throws android.os.RemoteException {
        return state(p0).density;
    }
    @Override public void setForcedDisplayDensityForUser(int p0, int p1, int p2) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setForcedDisplayDensityForUser");
    }
    @Override public void clearForcedDisplayDensityForUser(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: clearForcedDisplayDensityForUser");
    }
    @Override public void setForcedDisplayScalingMode(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setForcedDisplayScalingMode");
    }
    @Override public void setEventDispatching(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setEventDispatching");
    }
    @Override public boolean isWindowToken(android.os.IBinder p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isWindowToken");
    }
    @Override public void addWindowToken(android.os.IBinder p0, int p1, int p2, android.os.Bundle p3) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: addWindowToken");
    }
    @Override public void removeWindowToken(android.os.IBinder p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: removeWindowToken");
    }
    @Override public void setDisplayWindowRotationController(android.view.IDisplayWindowRotationController p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setDisplayWindowRotationController");
    }
    @Override public android.view.SurfaceControl addShellRoot(int p0, android.view.IWindow p1, int p2) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: addShellRoot");
    }
    @Override public void setShellRootAccessibilityWindow(int p0, int p1, android.view.IWindow p2) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setShellRootAccessibilityWindow");
    }
    @Override public void overridePendingAppTransitionMultiThumbFuture(android.view.IAppTransitionAnimationSpecsFuture p0, android.os.IRemoteCallback p1, boolean p2, int p3) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: overridePendingAppTransitionMultiThumbFuture");
    }
    @Override public void overridePendingAppTransitionRemote(android.view.RemoteAnimationAdapter p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: overridePendingAppTransitionRemote");
    }
    @Override public void endProlongedAnimations() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: endProlongedAnimations");
    }
    @Override public void startFreezingScreen(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: startFreezingScreen");
    }
    @Override public void stopFreezingScreen() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: stopFreezingScreen");
    }
    @Override public void disableKeyguard(android.os.IBinder p0, java.lang.String p1, int p2) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: disableKeyguard");
    }
    @Override public void reenableKeyguard(android.os.IBinder p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: reenableKeyguard");
    }
    @Override public void exitKeyguardSecurely(android.view.IOnKeyguardExitResult p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: exitKeyguardSecurely");
    }
    @Override public boolean isKeyguardLocked() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isKeyguardLocked");
    }
    @Override public boolean isKeyguardSecure(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isKeyguardSecure");
    }
    @Override public void dismissKeyguard(com.android.internal.policy.IKeyguardDismissCallback p0, java.lang.CharSequence p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: dismissKeyguard");
    }
    @Override public void addKeyguardLockedStateListener(com.android.internal.policy.IKeyguardLockedStateListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: addKeyguardLockedStateListener");
    }
    @Override public void removeKeyguardLockedStateListener(com.android.internal.policy.IKeyguardLockedStateListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: removeKeyguardLockedStateListener");
    }
    @Override public void setSwitchingUser(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setSwitchingUser");
    }
    @Override public void closeSystemDialogs(java.lang.String p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: closeSystemDialogs");
    }
    @Override public float getAnimationScale(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getAnimationScale");
    }
    @Override public float[] getAnimationScales() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getAnimationScales");
    }
    @Override public void setAnimationScale(int p0, float p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setAnimationScale");
    }
    @Override public void setAnimationScales(float[] p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setAnimationScales");
    }
    @Override public float getCurrentAnimatorScale() throws android.os.RemoteException {
        return state(0).animatorScale;
    }
    @Override public void setInTouchMode(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setInTouchMode");
    }
    @Override public void showStrictModeViolation(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: showStrictModeViolation");
    }
    @Override public void setStrictModeVisualIndicatorPreference(java.lang.String p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setStrictModeVisualIndicatorPreference");
    }
    @Override public void refreshScreenCaptureDisabled() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: refreshScreenCaptureDisabled");
    }
    @Override public void updateRotation(boolean p0, boolean p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: updateRotation");
    }
    @Override public int getDefaultDisplayRotation() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getDefaultDisplayRotation");
    }
    @Override public int watchRotation(android.view.IRotationWatcher p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: watchRotation");
    }
    @Override public void removeRotationWatcher(android.view.IRotationWatcher p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: removeRotationWatcher");
    }
    @Override public int getPreferredOptionsPanelGravity(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getPreferredOptionsPanelGravity");
    }
    @Override public void freezeRotation(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: freezeRotation");
    }
    @Override public void thawRotation() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: thawRotation");
    }
    @Override public boolean isRotationFrozen() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isRotationFrozen");
    }
    @Override public void freezeDisplayRotation(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: freezeDisplayRotation");
    }
    @Override public void thawDisplayRotation(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: thawDisplayRotation");
    }
    @Override public boolean isDisplayRotationFrozen(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isDisplayRotationFrozen");
    }
    @Override public void setFixedToUserRotation(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setFixedToUserRotation");
    }
    @Override public void setIgnoreOrientationRequest(int p0, boolean p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setIgnoreOrientationRequest");
    }
    @Override public android.graphics.Bitmap screenshotWallpaper() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: screenshotWallpaper");
    }
    @Override public android.view.SurfaceControl mirrorWallpaperSurface(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: mirrorWallpaperSurface");
    }
    @Override public boolean registerWallpaperVisibilityListener(android.view.IWallpaperVisibilityListener p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerWallpaperVisibilityListener");
    }
    @Override public void unregisterWallpaperVisibilityListener(android.view.IWallpaperVisibilityListener p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: unregisterWallpaperVisibilityListener");
    }
    @Override public void registerSystemGestureExclusionListener(android.view.ISystemGestureExclusionListener p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerSystemGestureExclusionListener");
    }
    @Override public void unregisterSystemGestureExclusionListener(android.view.ISystemGestureExclusionListener p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: unregisterSystemGestureExclusionListener");
    }
    @Override public boolean requestAssistScreenshot(android.app.IAssistDataReceiver p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: requestAssistScreenshot");
    }
    @Override public void hideTransientBars(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: hideTransientBars");
    }
    @Override public void setRecentsVisibility(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setRecentsVisibility");
    }
    @Override public void updateStaticPrivacyIndicatorBounds(int p0, android.graphics.Rect[] p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: updateStaticPrivacyIndicatorBounds");
    }
    @Override public void setNavBarVirtualKeyHapticFeedbackEnabled(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setNavBarVirtualKeyHapticFeedbackEnabled");
    }
    @Override public boolean hasNavigationBar(int p0) throws android.os.RemoteException {
        return state(p0).navigationBar;
    }
    @Override public int getNavBarPosition(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getNavBarPosition");
    }
    @Override public void lockNow(android.os.Bundle p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: lockNow");
    }
    @Override public boolean isSafeModeEnabled() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isSafeModeEnabled");
    }
    @Override public void enableScreenIfNeeded() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: enableScreenIfNeeded");
    }
    @Override public boolean clearWindowContentFrameStats(android.os.IBinder p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: clearWindowContentFrameStats");
    }
    @Override public android.view.WindowContentFrameStats getWindowContentFrameStats(android.os.IBinder p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getWindowContentFrameStats");
    }
    @Override public int getDockedStackSide() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getDockedStackSide");
    }
    @Override public void setDockedTaskDividerTouchRegion(android.graphics.Rect p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setDockedTaskDividerTouchRegion");
    }
    @Override public void registerPinnedTaskListener(int p0, android.view.IPinnedTaskListener p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerPinnedTaskListener");
    }
    @Override public void requestAppKeyboardShortcuts(com.android.internal.os.IResultReceiver p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: requestAppKeyboardShortcuts");
    }
    @Override public void getStableInsets(int p0, android.graphics.Rect p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getStableInsets");
    }
    @Override public void registerShortcutKey(long p0, com.android.internal.policy.IShortcutService p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerShortcutKey");
    }
    @Override public void createInputConsumer(android.os.IBinder p0, java.lang.String p1, int p2, android.view.InputChannel p3) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: createInputConsumer");
    }
    @Override public boolean destroyInputConsumer(java.lang.String p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: destroyInputConsumer");
    }
    @Override public android.graphics.Region getCurrentImeTouchRegion() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getCurrentImeTouchRegion");
    }
    @Override public void registerDisplayFoldListener(android.view.IDisplayFoldListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerDisplayFoldListener");
    }
    @Override public void unregisterDisplayFoldListener(android.view.IDisplayFoldListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: unregisterDisplayFoldListener");
    }
    @Override public int[] registerDisplayWindowListener(android.view.IDisplayWindowListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerDisplayWindowListener");
    }
    @Override public void unregisterDisplayWindowListener(android.view.IDisplayWindowListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: unregisterDisplayWindowListener");
    }
    @Override public void startWindowTrace() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: startWindowTrace");
    }
    @Override public void stopWindowTrace() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: stopWindowTrace");
    }
    @Override public void saveWindowTraceToFile() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: saveWindowTraceToFile");
    }
    @Override public boolean isWindowTraceEnabled() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isWindowTraceEnabled");
    }
    @Override public int getWindowingMode(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getWindowingMode");
    }
    @Override public void setWindowingMode(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setWindowingMode");
    }
    @Override public int getRemoveContentMode(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getRemoveContentMode");
    }
    @Override public void setRemoveContentMode(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setRemoveContentMode");
    }
    @Override public boolean shouldShowWithInsecureKeyguard(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: shouldShowWithInsecureKeyguard");
    }
    @Override public void setShouldShowWithInsecureKeyguard(int p0, boolean p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setShouldShowWithInsecureKeyguard");
    }
    @Override public boolean shouldShowSystemDecors(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: shouldShowSystemDecors");
    }
    @Override public void setShouldShowSystemDecors(int p0, boolean p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setShouldShowSystemDecors");
    }
    @Override public int getDisplayImePolicy(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getDisplayImePolicy");
    }
    @Override public void setDisplayImePolicy(int p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setDisplayImePolicy");
    }
    @Override public void syncInputTransactions(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: syncInputTransactions");
    }
    @Override public boolean isLayerTracing() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isLayerTracing");
    }
    @Override public void setLayerTracing(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setLayerTracing");
    }
    @Override public boolean mirrorDisplay(int p0, android.view.SurfaceControl p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: mirrorDisplay");
    }
    @Override public void setDisplayWindowInsetsController(int p0, android.view.IDisplayWindowInsetsController p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setDisplayWindowInsetsController");
    }
    @Override public void updateDisplayWindowRequestedVisibilities(int p0, android.view.InsetsVisibilities p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: updateDisplayWindowRequestedVisibilities");
    }
    @Override public boolean getWindowInsets(android.view.WindowManager.LayoutParams p0, int p1, android.view.InsetsState p2) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getWindowInsets");
    }
    @Override public java.util.List<android.view.DisplayInfo> getPossibleDisplayInfo(int p0, java.lang.String p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getPossibleDisplayInfo");
    }
    @Override public void showGlobalActions() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: showGlobalActions");
    }
    @Override public void setLayerTracingFlags(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setLayerTracingFlags");
    }
    @Override public void requestScrollCapture(int p0, android.os.IBinder p1, int p2, android.view.IScrollCaptureResponseListener p3) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: requestScrollCapture");
    }
    @Override public void holdLock(android.os.IBinder p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: holdLock");
    }
    @Override public java.lang.String[] getSupportedDisplayHashAlgorithms() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getSupportedDisplayHashAlgorithms");
    }
    @Override public android.view.displayhash.VerifiedDisplayHash verifyDisplayHash(android.view.displayhash.DisplayHash p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: verifyDisplayHash");
    }
    @Override public void setDisplayHashThrottlingEnabled(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setDisplayHashThrottlingEnabled");
    }
    @Override public android.content.res.Configuration attachWindowContextToDisplayArea(android.os.IBinder p0, int p1, int p2, android.os.Bundle p3) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: attachWindowContextToDisplayArea");
    }
    @Override public void attachWindowContextToWindowToken(android.os.IBinder p0, android.os.IBinder p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: attachWindowContextToWindowToken");
    }
    @Override public android.content.res.Configuration attachToDisplayContent(android.os.IBinder p0, int p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: attachToDisplayContent");
    }
    @Override public void detachWindowContextFromWindowContainer(android.os.IBinder p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: detachWindowContextFromWindowContainer");
    }
    @Override public boolean registerCrossWindowBlurEnabledListener(android.view.ICrossWindowBlurEnabledListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerCrossWindowBlurEnabledListener");
    }
    @Override public void unregisterCrossWindowBlurEnabledListener(android.view.ICrossWindowBlurEnabledListener p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: unregisterCrossWindowBlurEnabledListener");
    }
    @Override public boolean isTaskSnapshotSupported() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: isTaskSnapshotSupported");
    }
    @Override public int getImeDisplayId() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: getImeDisplayId");
    }
    @Override public void setTaskSnapshotEnabled(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setTaskSnapshotEnabled");
    }
    @Override public void setTaskTransitionSpec(android.view.TaskTransitionSpec p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setTaskTransitionSpec");
    }
    @Override public void clearTaskTransitionSpec() throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: clearTaskTransitionSpec");
    }
    @Override public void registerTaskFpsCallback(int p0, android.window.ITaskFpsCallback p1) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: registerTaskFpsCallback");
    }
    @Override public void unregisterTaskFpsCallback(android.window.ITaskFpsCallback p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: unregisterTaskFpsCallback");
    }
    @Override public android.graphics.Bitmap snapshotTaskForRecents(int p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: snapshotTaskForRecents");
    }
    @Override public void setRecentsAppBehindSystemBars(boolean p0) throws android.os.RemoteException {
        throw new UnsupportedOperationException("Unsupported Linux window API: setRecentsAppBehindSystemBars");
    }
}
