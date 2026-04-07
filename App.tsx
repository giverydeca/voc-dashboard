import React, { useEffect, useState } from 'react';
import Header from './components/Header';
import FileUploader from './components/FileUploader';
import PreviewTable from './components/PreviewTable';
import { CsvFile, OutputEntry, OutputRecord, ProcessingStatus } from './types';
import { processCsvFiles } from './services/openaiService';
import { downloadCsv, splitCsvByParts, splitCsvBySize } from './utils/csvHelper';
import { clearOutputs, deleteOutput, listOutputs, pruneOutputs, saveOutput } from './utils/outputStorage';

const App: React.FC = () => {
  const [files, setFiles] = useState<CsvFile[]>([]);
  const [prompt, setPrompt] = useState<string>('複数のCSVを1つに統合し、同じ意味の列は同じ列として揃えてください。');
  const [status, setStatus] = useState<ProcessingStatus>(ProcessingStatus.IDLE);
  const [resultOutputs, setResultOutputs] = useState<OutputEntry[]>([]);
  const [resultFilenameBase, setResultFilenameBase] = useState<string>('');
  const [parallelRequests, setParallelRequests] = useState<number>(12);
  const [model, setModel] = useState<string>('gpt-5.2');
  const [fastMode, setFastMode] = useState<boolean>(true);
  const [outputMode, setOutputMode] = useState<'combined' | 'perInput'>('combined');
  const [splitSizeMb, setSplitSizeMb] = useState<number>(10);
  const [splitByInputCount, setSplitByInputCount] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [storageError, setStorageError] = useState<string | null>(null);
  const [progressInfo, setProgressInfo] = useState<{ completed: number; total: number; status: string } | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);
  const [activeDropZone, setActiveDropZone] = useState<'input' | 'instructions' | null>(null);
  const [savedOutputs, setSavedOutputs] = useState<OutputRecord[]>([]);

  const buildId = () => {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      return crypto.randomUUID();
    }
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  };

  const buildFilenameBase = () => {
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    return `processed_output_${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(
      d.getMinutes()
    )}${pad(d.getSeconds())}`;
  };

  const refreshSavedOutputs = async () => {
    try {
      const outputs = await listOutputs();
      setSavedOutputs(outputs);
    } catch (err) {
      setStorageError('保存済み出力の読み込みに失敗しました。');
    }
  };

  useEffect(() => {
    void refreshSavedOutputs();
  }, []);

  const progressPercent = progressInfo
    ? progressInfo.total > 0
      ? Math.min(100, Math.round((progressInfo.completed / progressInfo.total) * 100))
      : progressInfo.status === 'complete'
        ? 100
        : 0
    : 0;

  const progressStatusLabel = (() => {
    if (!progressInfo) return '';
    switch (progressInfo.status) {
      case 'queued':
        return 'キュー待機中';
      case 'processing':
        return '処理中';
      case 'complete':
        return '完了';
      case 'cancelled':
        return 'キャンセル済み';
      case 'error':
        return 'エラー';
      default:
        return progressInfo.status;
    }
  })();

  const singleChunkNotice =
    progressInfo && progressInfo.status === 'processing' && progressInfo.total <= 1
      ? '※ データが 1 チャンクに収まっているため、完了までプログレスバーは更新されません。'
      : null;

  const handleFilesSelected = (newFiles: CsvFile[]) => {
    setFiles(prev => [...prev, ...newFiles]);
    setResultOutputs([]);
    setResultFilenameBase('');
    setErrorMsg(null);
    setStatus(ProcessingStatus.IDLE);
    setProgressInfo(null);
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleProcess = async () => {
    if (files.length === 0) return;
    
    setStatus(ProcessingStatus.PROCESSING);
    setErrorMsg(null);
    setResultOutputs([]);
    setResultFilenameBase('');
    setProgressInfo({ completed: 0, total: 0, status: 'queued' });
    setCurrentJobId(null);

    try {
      const { outputs } = await processCsvFiles(files, prompt, {
        maxConcurrentRequests: parallelRequests,
        model,
        onProgress: (info) => {
          setProgressInfo(info);
        },
        onJobStarted: (jobId) => {
          setCurrentJobId(jobId);
        },
        fastMode,
        outputMode,
      });

      const maxBytes = Math.max(1, Math.round(splitSizeMb * 1024 * 1024));
      const shouldSplitByCount =
        outputMode === 'combined' && splitByInputCount && files.length > 1;

      const outputEntries: OutputEntry[] = outputs.map((o, idx) => {
        const chunks = shouldSplitByCount
          ? splitCsvByParts(o.csv, files.length)
          : splitCsvBySize(o.csv, maxBytes);
        const label = o.label?.trim() ? o.label : `出力 ${idx + 1}`;
        return { label, chunks };
      });

      setResultOutputs(outputEntries);
      const filenameBase = buildFilenameBase();
      setResultFilenameBase(filenameBase);
      setStatus(ProcessingStatus.COMPLETE);
      setProgressInfo(null);
      setCurrentJobId(null);

      if (outputEntries.length > 0) {
        try {
          const record: OutputRecord = {
            id: buildId(),
            createdAt: Date.now(),
            filenameBase,
            outputs: outputEntries,
            chunks: outputEntries[0]?.chunks,
            model,
          };
          await saveOutput(record);
          await pruneOutputs(20);
          await refreshSavedOutputs();
        } catch (err) {
          setStorageError('出力の自動保存に失敗しました。ブラウザの保存容量をご確認ください。');
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "予期しないエラーが発生しました");
      if (err?.message?.includes("キャンセル")) {
        setStatus(ProcessingStatus.CANCELLED);
      } else {
        setStatus(ProcessingStatus.ERROR);
      }
      setProgressInfo(null);
      setCurrentJobId(null);
    }
  };

  const sanitizeFilename = (value: string) =>
    value.replace(/[^\w\-]+/g, '_').replace(/_{2,}/g, '_').replace(/^_+|_+$/g, '');

  const handleDownloadOutput = (output: OutputEntry, outputIndex: number, chunkIndex: number) => {
    const chunk = output.chunks[chunkIndex];
    if (!chunk) return;
    const safeLabel = sanitizeFilename(output.label || `output_${outputIndex + 1}`);
    const base = resultFilenameBase || 'processed_output';
    const nameBase = safeLabel ? `${base}_${safeLabel}` : base;
    const filename =
      output.chunks.length > 1
        ? `${nameBase}_part_${chunkIndex + 1}.csv`
        : `${nameBase}.csv`;
    downloadCsv(chunk, filename);
  };

  const handleDownloadSaved = (record: OutputRecord, entry: OutputEntry, entryIndex: number, chunkIndex: number) => {
    const chunk = entry.chunks[chunkIndex];
    if (!chunk) return;
    const safeLabel = sanitizeFilename(entry.label || `output_${entryIndex + 1}`);
    const nameBase = safeLabel ? `${record.filenameBase}_${safeLabel}` : record.filenameBase;
    const filename =
      entry.chunks.length > 1
        ? `${nameBase}_part_${chunkIndex + 1}.csv`
        : `${nameBase}.csv`;
    downloadCsv(chunk, filename);
  };

  const handleDeleteSaved = async (id: string) => {
    try {
      await deleteOutput(id);
      await refreshSavedOutputs();
    } catch (err) {
      setStorageError('保存データの削除に失敗しました。');
    }
  };

  const handleClearSaved = async () => {
    try {
      await clearOutputs();
      setSavedOutputs([]);
    } catch (err) {
      setStorageError('保存データの削除に失敗しました。');
    }
  };

  const buildCsvFilesFromFileList = async (fileList: FileList | File[]): Promise<CsvFile[]> => {
    const newFiles: CsvFile[] = [];
    const filesArray = Array.from(fileList as ArrayLike<File>);
    for (let i = 0; i < filesArray.length; i++) {
      const file = filesArray[i];
      if (!file || !file.name.toLowerCase().endsWith('.csv')) continue;
      const text = await file.text();
      newFiles.push({
        id: `${file.name}-${Date.now()}-${i}-${Math.random()}`,
        name: file.name,
        content: text,
        size: file.size,
      });
    }
    return newFiles;
  };

  const handleDroppedFiles = async (fileList?: FileList | File[]) => {
    if (!fileList || fileList.length === 0) return;
    const csvFiles = await buildCsvFilesFromFileList(fileList);
    if (csvFiles.length > 0) {
      handleFilesSelected(csvFiles);
    } else {
      setErrorMsg('CSV ファイルのみドロップできます。');
    }
  };

  const handleInstructionDrop = async (fileList?: FileList | File[]) => {
    if (!fileList || fileList.length === 0) return;
    const filesArray = Array.from(fileList as ArrayLike<File>);
    let combinedText = '';

    for (const file of filesArray) {
      if (!file) continue;
      const lower = file.name.toLowerCase();
      const isTextFile =
        lower.endsWith('.md') ||
        lower.endsWith('.markdown') ||
        lower.endsWith('.txt') ||
        file.type.startsWith('text/');

      if (!isTextFile) continue;

      const text = await file.text();
      if (text.trim().length > 0) {
        combinedText += `${text.trim()}\n\n`;
      }
    }

    if (combinedText) {
      setPrompt(prev => {
        const base = prev?.trim().length ? `${prev.trim()}\n\n` : '';
        return `${base}${combinedText.trim()}`;
      });
      setErrorMsg(null);
    } else {
      setErrorMsg('ドロップできるのはテキスト/Markdownファイルのみです。');
    }
  };

  const dragEventHasFiles = (event: React.DragEvent<HTMLDivElement>) => {
    const types = event.dataTransfer?.types;
    if (!types) return false;
    // DOMStringList in some browsers lacks includes(), so convert array-like manually.
    for (let i = 0; i < types.length; i++) {
      if (types[i] === 'Files') return true;
    }
    return false;
  };

  const makeDragOverHandler = (zone: 'input' | 'instructions') => (event: React.DragEvent<HTMLDivElement>) => {
    if (dragEventHasFiles(event)) {
      event.preventDefault();
      setActiveDropZone(zone);
    }
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node)) {
      setActiveDropZone(null);
    }
  };

  const makeDropHandler = (zone: 'input' | 'instructions') => async (event: React.DragEvent<HTMLDivElement>) => {
    if (!event.dataTransfer?.files?.length) return;
    event.preventDefault();
    setActiveDropZone(null);
    if (zone === 'input') {
      await handleDroppedFiles(event.dataTransfer.files);
    } else {
      await handleInstructionDrop(event.dataTransfer.files);
    }
  };

  const handleCancelProcessing = async () => {
    if (!currentJobId || status !== ProcessingStatus.PROCESSING) return;
    setIsCancelling(true);
    try {
      await fetch(`/api/process-csv/${currentJobId}/cancel`, { method: 'POST' });
      setStatus(ProcessingStatus.CANCELLED);
      setErrorMsg('処理を停止しました。');
      setProgressInfo(null);
      setResultOutputs([]);
      setResultFilenameBase('');
    } catch (err: any) {
      setErrorMsg(err?.message || '処理停止に失敗しました。');
    } finally {
      setCurrentJobId(null);
      setIsCancelling(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-grow p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto w-full space-y-8">
        
        {/* Step 1: アップロード */}
        <section
          className={`space-y-4 transition-colors ${activeDropZone === 'input' ? 'ring-2 ring-indigo-400 bg-indigo-50/60 rounded-xl' : ''}`}
          onDragOver={makeDragOverHandler('input')}
          onDragLeave={handleDragLeave}
          onDrop={makeDropHandler('input')}
        >
          <div className="flex justify-between items-baseline">
            <h2 className="text-lg font-semibold text-slate-800">1. 入力ファイル</h2>
            {files.length > 0 && (
              <button 
                onClick={() => setFiles([])} 
                className="text-xs text-red-500 hover:text-red-600 font-medium"
              >
                すべて削除
              </button>
            )}
          </div>
          
          <FileUploader onFilesSelected={handleFilesSelected} />

          {/* File List & Previews */}
          {files.length > 0 && (
            <div className="grid grid-cols-1 gap-6 mt-6">
              {files.map(file => (
                <div key={file.id} className="relative group">
                   <div className="absolute top-3 right-3 z-20">
                     <button 
                      onClick={() => removeFile(file.id)}
                      className="bg-white/90 p-1.5 rounded-full text-slate-400 hover:text-red-500 shadow-sm border border-slate-200"
                      title="Remove file"
                     >
                       <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                       </svg>
                     </button>
                   </div>
                   <PreviewTable title={file.name} content={file.content} maxHeight="max-h-48" />
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Step 2: 指示 */}
        <section
          className={`space-y-4 transition-opacity duration-300 ${files.length === 0 ? 'opacity-50' : 'opacity-100'} ${activeDropZone === 'instructions' ? 'ring-2 ring-indigo-400 bg-indigo-50/60 rounded-xl' : ''}`}
          onDragOver={makeDragOverHandler('instructions')}
          onDragLeave={handleDragLeave}
          onDrop={makeDropHandler('instructions')}
        >
          <h2 className="text-lg font-semibold text-slate-800">2. 処理内容の指示</h2>
          <div className="bg-white p-1 rounded-xl shadow-sm border border-slate-200">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-y min-h-[120px] text-slate-700 placeholder-slate-400"
              placeholder="例）ファイルを結合し、「Total」列を「Amount」にリネームして日付順にソートしてください。"
            />
            <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 rounded-b-lg flex justify-between items-center text-xs text-slate-500">
              <span>列の対応関係やフィルタ条件をできるだけ具体的に書いてください。</span>
              <span>{prompt.length} 文字</span>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs text-slate-600">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
              <div className="flex items-center gap-3">
                <span className="font-semibold text-slate-700">モデル</span>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="px-2 py-1 border border-slate-300 rounded-md text-sm bg-white"
                >
                  <option value="gpt-5.2">gpt-5.2（最新・高品質）</option>
                  <option value="gpt-5.1">gpt-5.1（高品質）</option>
                  <option value="gpt-5-mini">gpt-5-mini（高速・低コスト）</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <span className="font-semibold text-slate-700">並列リクエスト数</span>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={1}
                    max={80}
                    value={parallelRequests}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10);
                      if (Number.isNaN(v)) return;
                      setParallelRequests(v);
                    }}
                    className="w-32"
                  />
                  <span className="w-10 text-right font-semibold text-slate-700">
                    {parallelRequests}
                  </span>
                </div>
                <span className="text-[11px] text-slate-400">
                  値を上げるほど速くなりますが、コストと負荷も増え、API制限で失敗する場合があります。
                </span>
              </div>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 font-semibold text-slate-700 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={fastMode}
                    onChange={(e) => setFastMode(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 border-slate-300 rounded"
                  />
                  高速モード
                </label>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-semibold text-slate-700">出力モード</span>
                <select
                  value={outputMode}
                  onChange={(e) => {
                    const next = e.target.value === 'perInput' ? 'perInput' : 'combined';
                    setOutputMode(next);
                    if (next === 'perInput') {
                      setSplitByInputCount(false);
                    }
                  }}
                  className="px-2 py-1 border border-slate-300 rounded-md text-sm bg-white"
                >
                  <option value="combined">全入力を統合</option>
                  <option value="perInput">入力ごとに処理</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <span className="font-semibold text-slate-700">分割サイズ</span>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={1}
                    max={200}
                    value={splitSizeMb}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      if (Number.isNaN(v)) return;
                      setSplitSizeMb(v);
                    }}
                    className="w-20 px-2 py-1 border border-slate-300 rounded-md text-sm bg-white"
                  />
                  <span className="text-xs text-slate-500">MB</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <label className={`flex items-center gap-2 font-semibold cursor-pointer select-none ${outputMode === 'perInput' ? 'text-slate-400' : 'text-slate-700'}`}>
                  <input
                    type="checkbox"
                    checked={splitByInputCount}
                    onChange={(e) => setSplitByInputCount(e.target.checked)}
                    disabled={outputMode === 'perInput'}
                    className="h-4 w-4 text-indigo-600 border-slate-300 rounded"
                  />
                  入力数に合わせて分割
                </label>
              </div>
            </div>
            <div className="text-slate-500 sm:text-right">
              出力モードや分割サイズを調整できます（入力ごとに処理は個別CSV、入力数に合わせて分割は統合出力のみ）。
            </div>
          </div>
        </section>

        {/* Step 3: 実行 */}
        <section className={`pt-4 border-t border-slate-200 ${files.length === 0 ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
           <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
             <div className="text-sm text-slate-500">
               {files.length} 個のファイルが処理対象です
             </div>
             
             <div className="flex items-center gap-3">
               <button
                 onClick={handleProcess}
                 disabled={status === ProcessingStatus.PROCESSING}
                 className={`
                   relative px-8 py-3 rounded-lg font-semibold text-white shadow-lg shadow-indigo-500/30 transition-all
                   ${status === ProcessingStatus.PROCESSING 
                     ? 'bg-indigo-400 cursor-not-allowed' 
                     : 'bg-indigo-600 hover:bg-indigo-700 hover:translate-y-[-1px]'
                   }
                 `}
               >
                 {status === ProcessingStatus.PROCESSING ? (
                   <span className="flex items-center gap-2">
                     <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                       <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                       <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                     </svg>
                    処理中...
                   </span>
                 ) : (
                   'CSV を生成'
                 )}
               </button>

               {status === ProcessingStatus.PROCESSING && currentJobId && (
                 <button
                   onClick={handleCancelProcessing}
                   disabled={isCancelling}
                   className={`
                     px-6 py-3 rounded-lg font-semibold text-white shadow-md transition-all
                     ${isCancelling ? 'bg-slate-400 cursor-not-allowed' : 'bg-red-500 hover:bg-red-600'}
                   `}
                 >
                   {isCancelling ? '停止中...' : '処理停止'}
                 </button>
               )}
             </div>
           </div>
           
           {errorMsg && (
             <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm break-words whitespace-pre-wrap">
               エラー: {errorMsg}
             </div>
           )}
          {storageError && (
            <div className="mt-4 p-4 bg-amber-50 text-amber-700 rounded-lg border border-amber-200 text-sm break-words whitespace-pre-wrap">
              保存: {storageError}
            </div>
          )}

           {progressInfo && (
             <div className="w-full mt-4 space-y-2">
               <div className="flex items-center justify-between text-xs text-slate-500">
                 <span>{progressStatusLabel}</span>
                 <span>
                   {progressInfo.completed} / {progressInfo.total || '?'} チャンク
                 </span>
               </div>
               <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                 <div
                   className="h-2 bg-indigo-500 transition-all duration-300"
                   style={{ width: `${progressPercent}%` }}
                 ></div>
               </div>
              {singleChunkNotice && (
                <div className="text-[11px] text-slate-400">
                  {singleChunkNotice}
                </div>
              )}
             </div>
           )}
        </section>

        {/* Step 4: 結果 */}
        {resultOutputs.length > 0 && status === ProcessingStatus.COMPLETE && (
          <section className="space-y-4 animate-fade-in pt-8 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-emerald-700 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                結果が生成されました
              </h2>
              <div className="text-xs text-emerald-700">
                出力数: {resultOutputs.length}
              </div>
            </div>

            <div className="space-y-6">
              {resultOutputs.map((output, outputIndex) => (
                <div key={`${output.label}-${outputIndex}`} className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-slate-700">
                      {output.label}
                    </div>
                    <div className="text-xs text-slate-500">
                      チャンク: {output.chunks.length}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {output.chunks.map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleDownloadOutput(output, outputIndex, idx)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium shadow-sm transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        {output.chunks.length > 1 ? `パート ${idx + 1}` : 'CSV をダウンロード'}
                      </button>
                    ))}
                  </div>
                  <div className="bg-emerald-50/50 p-1 rounded-xl border border-emerald-100 mt-4">
                    <PreviewTable title={`${output.label} プレビュー`} content={output.chunks[0] ?? ''} maxHeight="max-h-96" />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {savedOutputs.length > 0 && (
          <section className="space-y-4 animate-fade-in pt-8 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">保存済み出力</h2>
              <button
                onClick={handleClearSaved}
                className="text-xs text-red-500 hover:text-red-600 font-medium"
              >
                すべて削除
              </button>
            </div>
            <div className="space-y-3">
              {savedOutputs.map((output) => {
                const entries = output.outputs ?? (output.chunks ? [{ label: '出力', chunks: output.chunks }] : []);
                return (
                  <div key={output.id} className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-slate-700">
                        {new Date(output.createdAt).toLocaleString()}
                      </div>
                      <button
                        onClick={() => handleDeleteSaved(output.id)}
                        className="text-xs text-slate-400 hover:text-red-500 font-medium"
                      >
                        削除
                      </button>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      モデル: {output.model || 'default'} / 出力: {entries.length}
                    </div>
                    <div className="space-y-3 mt-3">
                      {entries.map((entry, entryIndex) => (
                        <div key={`${entry.label}-${entryIndex}`} className="bg-slate-50/60 rounded-lg p-3 border border-slate-100">
                          <div className="text-xs font-semibold text-slate-600">{entry.label}</div>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {entry.chunks.map((_, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleDownloadSaved(output, entry, entryIndex, idx)}
                                className="flex items-center gap-2 px-3 py-1.5 bg-slate-600 hover:bg-slate-700 text-white rounded-lg text-xs font-medium shadow-sm transition-colors"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                {entry.chunks.length > 1 ? `パート ${idx + 1}` : 'CSV をダウンロード'}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

      </main>
    </div>
  );
};

export default App;
