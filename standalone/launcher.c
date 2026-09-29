#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <shobjidl.h>
#include <wchar.h>
#include <wctype.h>

#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "user32.lib")

#define SCRIPT_TOOLBOX_APP_ID L"ScriptToolbox.App"
#define SCRIPT_TOOLBOX_PATH_CAPACITY 32768

typedef int (__cdecl *PyMainFunction)(int, wchar_t **);

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

static int is_versioned_python_dll(const wchar_t *filename)
{
    const wchar_t *prefix = L"python3";
    const wchar_t *suffix = L".dll";
    size_t prefix_length = wcslen(prefix);
    size_t suffix_length = wcslen(suffix);
    size_t length = wcslen(filename);
    size_t index;

    if (length <= prefix_length + suffix_length) {
        return 0;
    }

    if (_wcsnicmp(filename, prefix, prefix_length) != 0) {
        return 0;
    }

    if (_wcsicmp(filename + length - suffix_length, suffix) != 0) {
        return 0;
    }

    for (
        index = prefix_length;
        index < length - suffix_length;
        ++index
    ) {
        if (!iswdigit(filename[index])) {
            return 0;
        }
    }

    return 1;
}

static int find_python_dll(
    const wchar_t *runtime_directory,
    wchar_t *python_dll,
    size_t python_dll_capacity
)
{
    wchar_t pattern[SCRIPT_TOOLBOX_PATH_CAPACITY];
    WIN32_FIND_DATAW find_data;
    HANDLE find_handle;
    int result = 0;

    if (swprintf_s(
        pattern,
        SCRIPT_TOOLBOX_PATH_CAPACITY,
        L"%ls\\python3*.dll",
        runtime_directory
    ) < 0) {
        return 0;
    }

    find_handle = FindFirstFileW(
        pattern,
        &find_data
    );
    if (find_handle == INVALID_HANDLE_VALUE) {
        return 0;
    }

    do {
        if (
            !(find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) &&
            is_versioned_python_dll(find_data.cFileName)
        ) {
            if (swprintf_s(
                python_dll,
                python_dll_capacity,
                L"%ls\\%ls",
                runtime_directory,
                find_data.cFileName
            ) >= 0) {
                result = 1;
            }
            break;
        }
    } while (FindNextFileW(
        find_handle,
        &find_data
    ));

    FindClose(
        find_handle
    );
    return result;
}

static void apply_app_user_model_id(void)
{
    /*
     * The Python standalone entry point applies the same ID as a fallback.
     * Set it here as well so Windows sees the native executable identity
     * before the embedded interpreter or Qt are initialized.
     */
    (void)SetCurrentProcessExplicitAppUserModelID(
        SCRIPT_TOOLBOX_APP_ID
    );
}

int WINAPI wWinMain(
    HINSTANCE instance,
    HINSTANCE previous_instance,
    PWSTR command_line,
    int show_command
)
{
    wchar_t executable_path[SCRIPT_TOOLBOX_PATH_CAPACITY];
    wchar_t root[SCRIPT_TOOLBOX_PATH_CAPACITY];
    wchar_t runtime_directory[SCRIPT_TOOLBOX_PATH_CAPACITY];
    wchar_t python_dll[SCRIPT_TOOLBOX_PATH_CAPACITY];
    wchar_t bootstrap[SCRIPT_TOOLBOX_PATH_CAPACITY];
    wchar_t *python_argv[2];
    HMODULE python_module;
    PyMainFunction py_main;
    DWORD module_length;
    int exit_code;

    (void)instance;
    (void)previous_instance;
    (void)command_line;
    (void)show_command;

    module_length = GetModuleFileNameW(
        NULL,
        executable_path,
        SCRIPT_TOOLBOX_PATH_CAPACITY
    );
    if (
        module_length == 0 ||
        module_length >= SCRIPT_TOOLBOX_PATH_CAPACITY
    ) {
        return show_error(
            L"Could not resolve the Script Toolbox executable path."
        );
    }

    if (wcscpy_s(
        root,
        SCRIPT_TOOLBOX_PATH_CAPACITY,
        executable_path
    ) != 0) {
        return show_error(
            L"Could not resolve the Script Toolbox directory."
        );
    }

    if (!parent_directory(root)) {
        return show_error(
            L"Could not resolve the Script Toolbox root directory."
        );
    }

    if (swprintf_s(
        runtime_directory,
        SCRIPT_TOOLBOX_PATH_CAPACITY,
        L"%ls\\runtime",
        root
    ) < 0) {
        return show_error(
            L"Could not build the portable runtime path."
        );
    }

    if (!find_python_dll(
        runtime_directory,
        python_dll,
        SCRIPT_TOOLBOX_PATH_CAPACITY
    )) {
        return show_error(
            L"Portable runtime is missing its versioned Python DLL."
        );
    }

    if (swprintf_s(
        bootstrap,
        SCRIPT_TOOLBOX_PATH_CAPACITY,
        L"%ls\\standalone\\bootstrap.py",
        root
    ) < 0) {
        return show_error(
            L"Could not build the standalone bootstrap path."
        );
    }

    if (GetFileAttributesW(bootstrap) == INVALID_FILE_ATTRIBUTES) {
        return show_error(
            L"Standalone bootstrap is missing: standalone\\bootstrap.py"
        );
    }

    apply_app_user_model_id();

    /*
     * Keep ScriptToolbox.exe as the actual process image. The previous
     * launcher spawned runtime\\pythonw.exe, which made Python the Windows
     * application identity and pin target. Loading the embeddable runtime DLL
     * in-process preserves the portable source/runtime layout while making the
     * native executable the owner of the Qt window and taskbar identity.
     */
    if (!SetDllDirectoryW(
        runtime_directory
    )) {
        return show_error(
            L"Could not configure the portable runtime DLL directory."
        );
    }

    python_module = LoadLibraryExW(
        python_dll,
        NULL,
        LOAD_WITH_ALTERED_SEARCH_PATH
    );
    if (python_module == NULL) {
        return show_error(
            L"Could not load the portable Python runtime."
        );
    }

    py_main = (PyMainFunction)GetProcAddress(
        python_module,
        "Py_Main"
    );
    if (py_main == NULL) {
        return show_error(
            L"Portable Python runtime does not export Py_Main."
        );
    }

    python_argv[0] = executable_path;
    python_argv[1] = bootstrap;

    exit_code = py_main(
        2,
        python_argv
    );

    return exit_code;
}
