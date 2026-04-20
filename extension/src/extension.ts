import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';
import { PythonBridge } from './python_bridge';
import { ControlPanelProvider } from './webview';

let pythonBridge: PythonBridge;
let controlPanelProvider: ControlPanelProvider;
let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel('Vibecode v6');

    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
    pythonBridge = new PythonBridge(workspaceRoot, outputChannel);
    controlPanelProvider = new ControlPanelProvider(context.extensionUri, pythonBridge);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            'vibecode.controlPanel',
            controlPanelProvider
        )
    );

    registerCommands(context);
    outputChannel.appendLine('Vibecode v6 activated successfully');
    controlPanelProvider.refreshStatus().catch(() => {});
}

function registerCommands(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.initWorkspace', async () => {
            await initWorkspace();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.prepareManualPhaseA', async () => {
            await prepareManualPhaseA();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.showPanel', () => {
            void vscode.commands.executeCommand('vibecode.controlPanel.focus');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.generatePlan', async () => {
            await runPhaseACommand('generate_plan');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.getClaudeFeedback', async () => {
            await runPhaseACommand('review_plan_claude');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.getGeminiFeedback', async () => {
            await runPhaseACommand('review_plan_gemini');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.synthesizeBlueprint', async () => {
            await runPhaseACommand('synthesize_blueprint');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.initTasks', async () => {
            await runPhaseBCommand('init');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.startLoop', async () => {
            await runPhaseBCommand('loop');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.stopLoop', async () => {
            pythonBridge.stopCurrentProcess();
            vscode.window.showInformationMessage('Vibecode: Loop stopped');
            await controlPanelProvider.refreshStatus();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.showStatus', async () => {
            await runPhaseBCommand('status');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('vibecode.resetState', async () => {
            await runPhaseBCommand('reset');
        })
    );
}

async function runPhaseACommand(command: string) {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const inputDir = path.join(workspaceRoot, '.aiwf', 'input');

    outputChannel.show();
    outputChannel.appendLine(`\n${'='.repeat(60)}`);
    outputChannel.appendLine(`Running: ${command}`);
    outputChannel.appendLine('='.repeat(60));

    try {
        let result = '';

        switch (command) {
            case 'generate_plan': {
                const goalFile = path.join(inputDir, 'goal.md');
                const planFile = path.join(inputDir, 'plan.md');
                if (!(await fileExists(goalFile))) {
                    vscode.window.showErrorMessage('goal.md not found. Run "Vibecode: Init Workspace" first.');
                    return;
                }
                result = await pythonBridge.generatePlan(goalFile, planFile);
                await openFile(planFile);
                vscode.window.showInformationMessage('Plan generated.');
                break;
            }
            case 'review_plan_claude': {
                const planFile = path.join(inputDir, 'plan.md');
                const feedbackFile = path.join(inputDir, 'feedback_1.md');
                if (!(await fileExists(planFile))) {
                    vscode.window.showErrorMessage('plan.md not found. Generate plan first.');
                    return;
                }
                result = await pythonBridge.reviewPlanClaude(planFile, feedbackFile);
                await openFile(feedbackFile);
                vscode.window.showInformationMessage('Claude feedback generated.');
                break;
            }
            case 'review_plan_gemini': {
                const planFile = path.join(inputDir, 'plan.md');
                const feedbackFile = path.join(inputDir, 'feedback_2.md');
                if (!(await fileExists(planFile))) {
                    vscode.window.showErrorMessage('plan.md not found. Generate plan first.');
                    return;
                }
                result = await pythonBridge.reviewPlanGemini(planFile, feedbackFile);
                await openFile(feedbackFile);
                vscode.window.showInformationMessage('Gemini feedback generated.');
                break;
            }
            case 'synthesize_blueprint': {
                const planFile = path.join(inputDir, 'plan.md');
                const feedback1 = path.join(inputDir, 'feedback_1.md');
                const feedback2 = path.join(inputDir, 'feedback_2.md');
                const blueprint = path.join(inputDir, 'blueprint.md');
                if (!(await fileExists(planFile)) || !(await fileExists(feedback1)) || !(await fileExists(feedback2))) {
                    vscode.window.showErrorMessage('Missing plan.md, feedback_1.md, or feedback_2.md.');
                    return;
                }
                result = await pythonBridge.synthesizeBlueprint(planFile, feedback1, feedback2, blueprint);
                await openFile(blueprint);
                vscode.window.showInformationMessage('Blueprint synthesized.');
                break;
            }
            default:
                vscode.window.showErrorMessage(`Unknown command: ${command}`);
                return;
        }

        outputChannel.appendLine(result);
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        showCommandError(errorMsg);
        outputChannel.appendLine(`ERROR: ${errorMsg}`);
    } finally {
        await controlPanelProvider.refreshStatus();
    }
}

async function runPhaseBCommand(command: string) {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    outputChannel.show();
    outputChannel.appendLine(`\n${'='.repeat(60)}`);
    outputChannel.appendLine(`Running: ${command}`);
    outputChannel.appendLine('='.repeat(60));

    try {
        const result = await pythonBridge.runOrchestrator(command);
        outputChannel.appendLine(result);

        if (command === 'loop' && result.toLowerCase().includes('completed')) {
            vscode.window.showInformationMessage('Vibecode: all tasks completed.');
        } else if (result.toLowerCase().includes('blocked')) {
            vscode.window.showWarningMessage('Vibecode: workflow blocked. Check review/log files.');
        }
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        showCommandError(errorMsg);
        outputChannel.appendLine(`ERROR: ${errorMsg}`);
    } finally {
        await controlPanelProvider.refreshStatus();
    }
}

async function initWorkspace() {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const inputDir = path.join(workspaceRoot, '.aiwf', 'input');
    const logsDir = path.join(workspaceRoot, '.aiwf', 'run', 'logs');
    const goalFile = path.join(inputDir, 'goal.md');

    await fs.mkdir(inputDir, { recursive: true });
    await fs.mkdir(logsDir, { recursive: true });

    if (!(await fileExists(goalFile))) {
        await fs.writeFile(goalFile, defaultGoalTemplate(), 'utf-8');
    }

    vscode.window.showInformationMessage('Workspace initialized. Fill .aiwf/input/goal.md to start.');
    await openFile(goalFile);
    await controlPanelProvider.refreshStatus();
}

async function prepareManualPhaseA() {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const inputDir = path.join(workspaceRoot, '.aiwf', 'input');
    await fs.mkdir(inputDir, { recursive: true });

    const files = [
        { name: 'plan.md', content: '# Plan\n\n' },
        { name: 'feedback_1.md', content: '# Feedback 1 (Claude)\n\n' },
        { name: 'feedback_2.md', content: '# Feedback 2 (Gemini)\n\n' },
        { name: 'blueprint.md', content: '# Blueprint\n\n' }
    ];

    for (const file of files) {
        const filePath = path.join(inputDir, file.name);
        if (!(await fileExists(filePath))) {
            await fs.writeFile(filePath, file.content, 'utf-8');
        }
    }

    const checklistPath = path.join(inputDir, 'PHASE_A_MANUAL_CHECKLIST.md');
    await fs.writeFile(checklistPath, manualPhaseAChecklist(), 'utf-8');
    await openFile(checklistPath);

    vscode.window.showInformationMessage('Manual Phase A checklist prepared.');
    await controlPanelProvider.refreshStatus();
}

function showCommandError(errorMsg: string) {
    if (/auth(entication)? failed|not logged in|login required|please log in|please login|expired credential|expired token|unauthorized/i.test(errorMsg)) {
        vscode.window.showErrorMessage('Authentication failed. Re-run login for your CLI tools, then retry.');
        return;
    }

    if (/not recognized as an internal or external command|no such file or directory|cannot find the file specified|enoent|command not found/i.test(errorMsg)) {
        vscode.window.showErrorMessage('Required CLI not found. Verify Python, Codex/Claude, and Gemini are available in PATH.');
        return;
    }

    vscode.window.showErrorMessage(`Error: ${errorMsg}`);
}

async function fileExists(filePath: string): Promise<boolean> {
    try {
        await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
        return true;
    } catch {
        return false;
    }
}

async function openFile(filePath: string) {
    try {
        const doc = await vscode.workspace.openTextDocument(filePath);
        await vscode.window.showTextDocument(doc);
    } catch {
        outputChannel.appendLine(`Could not open file: ${filePath}`);
    }
}

function defaultGoalTemplate(): string {
    return `# Goal: [Project Name]

## Objective
[Describe the final outcome.]

## Scope
### In Scope
- [Feature 1]
- [Feature 2]

### Out of Scope
- [Not included 1]

## Constraints
- [Constraint 1]
- [Constraint 2]

## Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
`;
}

function manualPhaseAChecklist(): string {
    return `# Phase A Manual Checklist

1. Write or update \`goal.md\`.
2. Ask Brain (GPT-5.4) to generate \`plan.md\`.
3. Send \`plan.md\` to Claude web chat and save as \`feedback_1.md\`.
4. Send \`plan.md\` to Gemini web chat and save as \`feedback_2.md\`.
5. Ask Brain (GPT-5.4) to synthesize into \`blueprint.md\`.
6. Run \`Vibecode: Init Tasks\`.
`;
}

export function deactivate() {
    pythonBridge?.dispose();
}
