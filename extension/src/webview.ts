import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';
import { PythonBridge } from './python_bridge';

type DashboardStatus = {
    workspaceRoot: string;
    goalExists: boolean;
    planExists: boolean;
    feedback1Exists: boolean;
    feedback2Exists: boolean;
    blueprintExists: boolean;
    tasksExists: boolean;
    stateExists: boolean;
    executionStatus: string;
    currentTask: string;
    completedCount: number;
    totalTasks: number;
    message: string;
};

export class ControlPanelProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'vibecode.controlPanel';
    private view?: vscode.WebviewView;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly pythonBridge: PythonBridge
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this.view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri]
        };

        webviewView.webview.html = this.getHtmlForWebview();

        webviewView.webview.onDidReceiveMessage(async (data: { type: string; command?: string; args?: string }) => {
            if (data.type === 'command' && data.command) {
                if (data.args) {
                    await vscode.commands.executeCommand(data.command, data.args);
                } else {
                    await vscode.commands.executeCommand(data.command);
                }
                return;
            }

            if (data.type === 'refreshStatus') {
                await this.refreshStatus();
            }
        });

        void this.refreshStatus();
    }

    public async refreshStatus(): Promise<void> {
        if (!this.view) {
            return;
        }

        const status = await this.getStatusSnapshot();
        this.view.webview.postMessage({
            type: 'status',
            payload: status
        });
    }

    private async getStatusSnapshot(): Promise<DashboardStatus> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        if (!workspaceRoot) {
            return {
                workspaceRoot: '(no workspace)',
                goalExists: false,
                planExists: false,
                feedback1Exists: false,
                feedback2Exists: false,
                blueprintExists: false,
                tasksExists: false,
                stateExists: false,
                executionStatus: 'not_initialized',
                currentTask: '-',
                completedCount: 0,
                totalTasks: 0,
                message: 'Open a folder to start.'
            };
        }

        const inputDir = path.join(workspaceRoot, '.aiwf', 'input');
        const runDir = path.join(workspaceRoot, '.aiwf', 'run');

        const goalPath = path.join(inputDir, 'goal.md');
        const planPath = path.join(inputDir, 'plan.md');
        const feedback1Path = path.join(inputDir, 'feedback_1.md');
        const feedback2Path = path.join(inputDir, 'feedback_2.md');
        const blueprintPath = path.join(inputDir, 'blueprint.md');
        const tasksPath = path.join(runDir, 'tasks.json');
        const statePath = path.join(runDir, 'state.json');

        const goalExists = await this.exists(goalPath);
        const planExists = await this.exists(planPath);
        const feedback1Exists = await this.exists(feedback1Path);
        const feedback2Exists = await this.exists(feedback2Path);
        const blueprintExists = await this.exists(blueprintPath);
        const tasksExists = await this.exists(tasksPath);
        const stateExists = await this.exists(statePath);

        let executionStatus = stateExists ? 'planning_complete' : 'not_initialized';
        let currentTask = '-';
        let completedCount = 0;
        let totalTasks = 0;

        if (stateExists) {
            try {
                const raw = await fs.readFile(statePath, 'utf-8');
                const parsed = JSON.parse(raw) as {
                    status?: string;
                    current_task_index?: number;
                    completed_tasks?: unknown[];
                    metadata?: { total_tasks?: number };
                };
                executionStatus = parsed.status || executionStatus;
                totalTasks = parsed.metadata?.total_tasks || 0;
                completedCount = parsed.completed_tasks?.length || 0;
                const currentIdx = parsed.current_task_index ?? 0;
                currentTask = totalTasks > 0 ? `${Math.min(currentIdx + 1, totalTasks)}/${totalTasks}` : '-';
            } catch {
                executionStatus = 'state_parse_error';
            }
        }

        const message = this.computeHint({
            goalExists,
            planExists,
            feedback1Exists,
            feedback2Exists,
            blueprintExists,
            tasksExists,
            stateExists,
            executionStatus
        });

        return {
            workspaceRoot,
            goalExists,
            planExists,
            feedback1Exists,
            feedback2Exists,
            blueprintExists,
            tasksExists,
            stateExists,
            executionStatus,
            currentTask,
            completedCount,
            totalTasks,
            message
        };
    }

    private computeHint(input: {
        goalExists: boolean;
        planExists: boolean;
        feedback1Exists: boolean;
        feedback2Exists: boolean;
        blueprintExists: boolean;
        tasksExists: boolean;
        stateExists: boolean;
        executionStatus: string;
    }): string {
        if (!input.goalExists) {
            return 'Run "Init Workspace", then fill goal.md.';
        }
        if (!input.planExists) {
            return 'Generate plan or create plan.md manually.';
        }
        if (!input.feedback1Exists || !input.feedback2Exists) {
            return 'Complete manual reviews and save feedback_1.md + feedback_2.md.';
        }
        if (!input.blueprintExists) {
            return 'Synthesize blueprint.md.';
        }
        if (!input.tasksExists || !input.stateExists) {
            return 'Run "Init Tasks" to create tasks/state.';
        }
        if (input.executionStatus === 'blocked') {
            return 'Execution is blocked. Check review.json and test_output.txt.';
        }
        if (input.executionStatus === 'completed') {
            return 'Execution completed.';
        }
        return 'Ready to run Phase B loop.';
    }

    private async exists(filePath: string): Promise<boolean> {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    private getHtmlForWebview(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibecode v6 Control Panel</title>
    <style>
        body {
            padding: 10px;
            color: var(--vscode-foreground);
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
        }

        h2 {
            margin-top: 18px;
            margin-bottom: 8px;
            color: var(--vscode-textLink-foreground);
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 4px;
        }

        .phase { margin-bottom: 18px; }

        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 12px;
            margin: 4px 0;
            cursor: pointer;
            width: 100%;
            text-align: left;
            border-radius: 2px;
            font-size: 12px;
        }

        button:hover { background-color: var(--vscode-button-hoverBackground); }

        .button-group {
            display: flex;
            gap: 8px;
            margin: 4px 0;
        }

        .button-group button {
            width: auto;
            flex: 1;
        }

        .status-section {
            background-color: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            padding: 8px;
            border-radius: 4px;
            margin-top: 10px;
        }

        .mono {
            font-family: var(--vscode-editor-font-family);
            font-size: 11px;
        }

        .badge {
            display: inline-block;
            margin-right: 6px;
            margin-bottom: 4px;
            padding: 2px 6px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 12px;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <h1>Vibecode v6</h1>

    <div class="phase">
        <h2>Workspace</h2>
        <button onclick="runCommand('vibecode.initWorkspace')">Init Workspace</button>
        <button onclick="runCommand('vibecode.prepareManualPhaseA')">Prepare Manual Phase A</button>
        <button onclick="runCommand('workbench.action.openSettings', 'vibecode')">Open Vibecode Settings</button>
    </div>

    <div class="phase">
        <h2>Phase A</h2>
        <button onclick="runCommand('vibecode.generatePlan')">Generate Plan</button>
        <button onclick="runCommand('vibecode.getClaudeFeedback')">Get Claude Feedback</button>
        <button onclick="runCommand('vibecode.getGeminiFeedback')">Get Gemini Feedback</button>
        <button onclick="runCommand('vibecode.synthesizeBlueprint')">Synthesize Blueprint</button>
    </div>

    <div class="phase">
        <h2>Phase B</h2>
        <button onclick="runCommand('vibecode.initTasks')">Init Tasks</button>
        <div class="button-group">
            <button onclick="runCommand('vibecode.startLoop')">Start Loop</button>
            <button onclick="runCommand('vibecode.stopLoop')">Stop</button>
        </div>
        <button onclick="runCommand('vibecode.showStatus')">Show Status</button>
        <button onclick="runCommand('vibecode.resetState')">Reset State</button>
    </div>

    <div class="status-section">
        <div class="button-group">
            <button onclick="refreshStatus()">Refresh Dashboard</button>
        </div>
        <p class="mono"><strong>Workspace:</strong> <span id="workspaceRoot">-</span></p>
        <div id="badges"></div>
        <p class="mono"><strong>Execution:</strong> <span id="execution">-</span></p>
        <p class="mono"><strong>Current Task:</strong> <span id="currentTask">-</span></p>
        <p class="mono"><strong>Completed:</strong> <span id="completed">-</span></p>
        <p class="mono"><strong>Hint:</strong> <span id="hint">-</span></p>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function runCommand(command, args) {
            if (command === 'workbench.action.openSettings') {
                vscode.postMessage({ type: 'command', command: 'workbench.action.openSettings', args });
                return;
            }
            vscode.postMessage({ type: 'command', command });
        }

        function refreshStatus() {
            vscode.postMessage({ type: 'refreshStatus' });
        }

        function badge(label, ok) {
            return '<span class="badge">' + (ok ? 'OK' : 'MISSING') + ' ' + label + '</span>';
        }

        window.addEventListener('message', event => {
            const msg = event.data;
            if (!msg || msg.type !== 'status') return;
            const s = msg.payload;
            document.getElementById('workspaceRoot').textContent = s.workspaceRoot;
            document.getElementById('execution').textContent = s.executionStatus;
            document.getElementById('currentTask').textContent = s.currentTask;
            document.getElementById('completed').textContent = s.completedCount + '/' + s.totalTasks;
            document.getElementById('hint').textContent = s.message;
            document.getElementById('badges').innerHTML =
                badge('goal.md', s.goalExists) +
                badge('plan.md', s.planExists) +
                badge('feedback_1.md', s.feedback1Exists) +
                badge('feedback_2.md', s.feedback2Exists) +
                badge('blueprint.md', s.blueprintExists) +
                badge('tasks.json', s.tasksExists) +
                badge('state.json', s.stateExists);
        });

        refreshStatus();
    </script>
</body>
</html>`;
    }
}
