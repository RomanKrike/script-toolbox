#define UNICODE
#define _UNICODE

#include <windows.h>
#include <wchar.h>

#pragma comment(lib, "user32.lib")

static int show_error(const wchar_t *message)
{
    MessageBoxW(
        NULL,
        message,
        L"Script Toolbox - Startup Error",
        MB_OK | MB_ICONERROR
    );
    return 1;
}

static int parent_directory(wchar_t *path)
{
    wchar_t *slash = wcsrchr(path, L'\\');

    if (slash == NULL) {
        return 0;
    }

    *slash = L'\0';
    return 1;
}

int WINAPI wWinMain(
    HINSTANCE instance,
    HINSTANCE previous_instance,
    PWSTR command_line,
    int show_command
)
{
    wchar_t root[MAX_PATH];
    wchar_t python_exe[MAX_PATH];
    wchar_t bootstrap[MAX_PATH];
    wchar_t child_command[MAX_PATH * 3];
    STARTUPINFOW startup_info;
    PROCESS_INFORMATION process_info;
    DWORD exit_code = 1;

    (void)instance;
    (void)previous_instance;
    (void)command_line;
    (void)show_command;

    if (GetModuleFileNameW(NULL, root, MAX_PATH) == 0) {
        return show_error(L"Could not resolve the Script Toolbox directory.");
    }

    if (!parent_directory(root)) {
        return show_error(L"Could not resolve the Script Toolbox root directory.");
    }

    if (swprintf(
        python_exe,
        MAX_PATH,
        L"%ls\\runtime\\pythonw.exe",
        root
    ) < 0) {
        return show_error(L"Could not build the portable Python path.");
    }

    if (swprintf(
        bootstrap,
        MAX_PATH,
        L"%ls\\standalone\\bootstrap.py",
        root
    ) < 0) {
        return show_error(L"Could not build the standalone bootstrap path.");
    }

    if (GetFileAttributesW(python_exe) == INVALID_FILE_ATTRIBUTES) {
        return show_error(
            L"Portable runtime is missing: runtime\\pythonw.exe"
        );
    }

    if (GetFileAttributesW(bootstrap) == INVALID_FILE_ATTRIBUTES) {
        return show_error(
            L"Standalone bootstrap is missing: standalone\\bootstrap.py"
        );
    }

    if (swprintf(
        child_command,
        MAX_PATH * 3,
        L"\"%ls\" \"%ls\"",
        python_exe,
        bootstrap
    ) < 0) {
        return show_error(L"Could not build the standalone command line.");
    }

    ZeroMemory(&startup_info, sizeof(startup_info));
    startup_info.cb = sizeof(startup_info);
    ZeroMemory(&process_info, sizeof(process_info));

    if (!CreateProcessW(
        python_exe,
        child_command,
        NULL,
        NULL,
        FALSE,
        CREATE_UNICODE_ENVIRONMENT,
        NULL,
        NULL,
        &startup_info,
        &process_info
    )) {
        return show_error(L"Could not start the portable Python runtime.");
    }

    WaitForSingleObject(process_info.hProcess, INFINITE);
    GetExitCodeProcess(process_info.hProcess, &exit_code);

    CloseHandle(process_info.hThread);
    CloseHandle(process_info.hProcess);

    return (int)exit_code;
}
