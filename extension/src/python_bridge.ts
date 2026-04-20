import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

export class PythonBridge {
    private currentProcess: ChildProcess | null = null;
    private workspaceRoot: string;
    private outputChannel: vscode.OutputChannel;
    private pythonPath: string;
    private scriptsDir: string;

    constructor(workspaceRoot: string, outputChannel: vscode.OutputChannel) {
        this.workspaceRoot = workspaceRoot;
        this.outputChannel = outputChannel;
        this.pythonPath = this.resolvePythonPath();
        this.scriptsDir = this.resolveScriptsDir(workspaceRoot);
        this.outputChannel.appendLine(`Python path: ${this.pythonPath}`);
        this.outputChannel.appendLine(`Scripts dir: ${this.scriptsDir}`);
    }

    private getConfig() {
        return vscode.workspace.getConfiguration('vibecode');
    }

    private resolvePythonPath(): string {
        const settingValue = this.getConfig().get<string>('pythonPath', '').trim();
        if (settingValue) {
            return settingValue;
        }

        const configured = process.env.VIBECODE_PYTHON_PATH;
        if (configured && configured.trim()) {
            return configured.trim();
        }

        return os.platform() === 'win32' ? 'python' : 'python3';
    }

    private resolveScriptsDir(workspaceRoot: string): string {
        const candidates: string[] = [];
        const settingValue = this.getConfig().get<string>('scriptsDir', '').trim();
        const configured = process.env.VIBECODE_SCRIPTS_DIR;

        if (settingValue) {
            candidates.push(path.resolve(settingValue));
        }
        if (configured && configured.trim()) {
            candidates.push(path.resolve(configured.trim()));
        }

        if (workspaceRoot) {
            candidates.push(path.join(workspaceRoot, 'python'));
            candidates.push(path.join(workspaceRoot, '..', 'vibecode-v6', 'python'));
            candidates.push(path.join(workspaceRoot, '..', 'vibecode-v6-updated', 'python'));
        }

        candidates.push(path.resolve(__dirname, '..', '..', 'python'));

        for (const candidate of candidates) {
            if (this.isScriptsDir(candidate)) {
                return candidate;
            }
        }

        throw new Error(
            'Could not locate Python scripts directory. Set VIBECODE_SCRIPTS_DIR to a folder containing orchestrator.py.'
        );
    }

    private refreshRuntimePaths() {
        this.pythonPath = this.resolvePythonPath();
        this.scriptsDir = this.resolveScriptsDir(this.workspaceRoot);
    }

    private buildRuntimeEnv(): NodeJS.ProcessEnv {
        const env: NodeJS.ProcessEnv = { ...process.env, PYTHONUNBUFFERED: '1' };
        const config = this.getConfig();

        const pythonPath = config.get<string>('pythonPath', '').trim();
        const scriptsDir = config.get<string>('scriptsDir', '').trim();
        const brainCli = config.get<string>('brainCli', '').trim();
        const brainPhaseAModel = config.get<string>('brainPhaseAModel', '').trim();
        const reviewerModel = config.get<string>('reviewerModel', '').trim();
        const coderCli = config.get<string>('coderCli', '').trim();
        const coderModel = config.get<string>('coderModel', '').trim();
        const adapterMode = config.get<string>('brainAdapterMode', '').trim();

        if (pythonPath) env.VIBECODE_PYTHON_PATH = pythonPath;
        if (scriptsDir) env.VIBECODE_SCRIPTS_DIR = scriptsDir;
        if (brainCli) env.VIBECODE_BRAIN_CLI = brainCli;
        if (brainPhaseAModel) env.VIBECODE_BRAIN_PHASE_A_MODEL = brainPhaseAModel;
        if (reviewerModel) env.VIBECODE_REVIEWER_MODEL = reviewerModel;
        if (coderCli) env.VIBECODE_CODER_CLI = coderCli;
        if (coderModel || coderModel === '') env.VIBECODE_CODER_MODEL = coderModel;
        if (adapterMode) env.VIBECODE_BRAIN_ADAPTER_MODE = adapterMode;

        return env;
    }

    private isScriptsDir(dirPath: string): boolean {
        try {
            const orchestratorPath = path.join(dirPath, 'orchestrator.py');
            const wrappersPath = path.join(dirPath, 'cli_wrappers.py');
            return fs.existsSync(orchestratorPath) && fs.existsSync(wrappersPath);
        } catch {
            return false;
        }
    }

    private async runPythonScript(
        scriptName: string,
        args: string[] = [],
        streamOutput: boolean = true
    ): Promise<string> {
        this.refreshRuntimePaths();
        this.outputChannel.appendLine(`Python path: ${this.pythonPath}`);
        this.outputChannel.appendLine(`Scripts dir: ${this.scriptsDir}`);

        return new Promise((resolve, reject) => {
            const scriptPath = path.join(this.scriptsDir, scriptName);
            
            this.currentProcess = spawn(this.pythonPath, [scriptPath, ...args], {
                cwd: this.scriptsDir,
                env: this.buildRuntimeEnv()
            });

            let stdout = '';
            let stderr = '';

            this.currentProcess.stdout?.on('data', (data) => {
                const text = data.toString();
                stdout += text;
                if (streamOutput) {
                    this.outputChannel.append(text);
                }
            });

            this.currentProcess.stderr?.on('data', (data) => {
                const text = data.toString();
                stderr += text;
                if (streamOutput) {
                    this.outputChannel.append(`[ERROR] ${text}`);
                }
            });

            this.currentProcess.on('close', (code) => {
                this.currentProcess = null;
                
                if (code === 0) {
                    resolve(stdout);
                } else {
                    reject(new Error(this.formatProcessError(code, stderr || stdout)));
                }
            });

            this.currentProcess.on('error', (error) => {
                this.currentProcess = null;
                reject(new Error(this.formatSpawnError(error)));
            });
        });
    }

    private formatProcessError(code: number | null, rawOutput: string): string {
        const detail = rawOutput.trim();
        const headline = `Process exited with code ${code ?? 'unknown'}`;

        if (this.isLikelyAuthError(detail)) {
            return `${headline}\n${detail}\n\nAuthentication appears to be missing or expired. Re-run \`claude login\` and/or \`gemini login\`, then try again.`;
        }

        if (this.isMissingCommandError(detail)) {
            return `${headline}\n${detail}\n\nRequired CLI is not available in PATH. Install the configured Claude/Gemini CLI tools or adjust your environment variables.`;
        }

        return detail ? `${headline}\n${detail}` : headline;
    }

    private formatSpawnError(error: Error & { code?: string }): string {
        const detail = error.message?.trim() || String(error);

        if (error.code === 'ENOENT' || this.isMissingCommandError(detail)) {
            return `${detail}\n\nPython or one of the configured AI CLIs could not be started. Verify \`VIBECODE_PYTHON_PATH\`, \`VIBECODE_BRAIN_CLI\`, and \`VIBECODE_CODER_CLI\`.`;
        }

        return detail;
    }

    private isLikelyAuthError(text: string): boolean {
        return /auth(entication)? failed|not logged in|login required|please log in|please login|expired credential|expired token|unauthorized|invalid api key|oauth/i.test(text);
    }

    private isMissingCommandError(text: string): boolean {
        return /not recognized as an internal or external command|no such file or directory|cannot find the file specified|enoent|command not found/i.test(text);
    }

    private async runPythonFunction(
        moduleName: string,
        functionName: string,
        functionArgs: string[]
    ): Promise<string> {
        const serializedArgs = functionArgs.map(arg => JSON.stringify(arg)).join(', ');
        const pythonCode = `
from ${moduleName} import ${functionName}
result = ${functionName}(${serializedArgs})
print(result)
`;

        const tempFile = path.join(this.scriptsDir, `_temp_runner_${Date.now()}_${Math.random().toString(16).slice(2)}.py`);
        fs.writeFileSync(tempFile, pythonCode, { encoding: 'utf-8' });

        try {
            const result = await this.runPythonScript(path.basename(tempFile));
            fs.unlinkSync(tempFile);
            return result;
        } catch (error) {
            fs.unlinkSync(tempFile);
            throw error;
        }
    }

    // Phase A functions
    async generatePlan(goalFile: string, outputFile: string): Promise<string> {
        this.outputChannel.appendLine('Calling Brain to generate plan...');
        return this.runPythonFunction('cli_wrappers', 'generate_plan', [goalFile, outputFile]);
    }

    async reviewPlanClaude(planFile: string, outputFile: string): Promise<string> {
        this.outputChannel.appendLine('Calling Claude to review plan...');
        return this.runPythonFunction('cli_wrappers', 'review_plan_claude', [planFile, outputFile]);
    }

    async reviewPlanGemini(planFile: string, outputFile: string): Promise<string> {
        this.outputChannel.appendLine('Calling Gemini to review plan...');
        return this.runPythonFunction('cli_wrappers', 'review_plan_gemini', [planFile, outputFile]);
    }

    async synthesizeBlueprint(
        planFile: string,
        feedback1File: string,
        feedback2File: string,
        outputFile: string
    ): Promise<string> {
        this.outputChannel.appendLine('Calling Brain to synthesize blueprint...');
        return this.runPythonFunction(
            'cli_wrappers',
            'synthesize_blueprint',
            [planFile, feedback1File, feedback2File, outputFile]
        );
    }

    // Phase B functions
    async runOrchestrator(command: string): Promise<string> {
        this.outputChannel.appendLine(`Running orchestrator command: ${command}`);
        return this.runPythonScript('orchestrator.py', [command], true);
    }

    stopCurrentProcess() {
        if (this.currentProcess) {
            this.currentProcess.kill();
            this.outputChannel.appendLine('Process killed');
        }
    }

    dispose() {
        this.stopCurrentProcess();
    }
}
