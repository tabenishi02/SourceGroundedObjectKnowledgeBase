using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;

// Compiled locally with fixed Python/script paths; never launches page-supplied commands.
class Launcher {
    static async Task Pump(Stream source, Stream target) {
        var buffer = new byte[8192];
        int count;
        while ((count = await source.ReadAsync(buffer, 0, buffer.Length)) != 0) {
            await target.WriteAsync(buffer, 0, count);
            await target.FlushAsync();
        }
    }
    static int Main(string[] args) {
        try {
            if (args.Length < 1 || !System.Text.RegularExpressions.Regex.IsMatch(args[0], "^chrome-extension://[a-p]{32}/$")) return 1;
            var start = new ProcessStartInfo(@"__PYTHON__", "-I -u \"" + @"__HOST__" + "\" " + args[0]);
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            start.RedirectStandardInput = true;
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;
            using (var child = Process.Start(start)) {
                Pump(Console.OpenStandardInput(), child.StandardInput.BaseStream).ContinueWith(t => child.StandardInput.Close());
                var output = Pump(child.StandardOutput.BaseStream, Console.OpenStandardOutput());
                var errors = Pump(child.StandardError.BaseStream, Console.OpenStandardError());
                child.WaitForExit();
                Task.WaitAll(output, errors);
                return child.ExitCode;
            }
        } catch { return 1; }
    }
}
