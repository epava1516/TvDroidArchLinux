/* Optional diagnostics only: use original liblog APIs to redirect its messages
 * to the original stderr logger. No JNI, service or success result substituted.
 * Remove this preload from functional acceptance runs.
 */
#ifndef __ANDROID__
#error Android Bionic target required
#endif
struct __android_log_message;
typedef void (*logger_function)(const struct __android_log_message*);
extern void __android_log_set_logger(logger_function);
extern void __android_log_stderr_logger(const struct __android_log_message*);
extern int __android_log_set_minimum_priority(int);
__attribute__((constructor)) static void select_stderr(void) {
  __android_log_set_logger(__android_log_stderr_logger);
  __android_log_set_minimum_priority(2);
}
