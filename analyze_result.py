# analyze_result_enhanced.py - 提取上述核心指标
#!/usr/bin/env python3
import re
import glob
import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# 正则模式（适配你的日志格式）
# ============================================================================

PATTERNS = {
    'iteration': re.compile(r'^\s*(\d+):\s*x\s*=\s*'),  # N: x = ...
    'distance': re.compile(r'dist\(lhs,rhs\)\s*=\s*[\d.eE+-]+,[\d.eE+-]+,([\d.eE+-]+)'),
    'branch': re.compile(r'\((\d+),([01])\)'),
    'choice': re.compile(r'\|\s*choice\s*=\s*(\d+)'),
    'penalty': re.compile(r'\|\s*__r\s*=\s*([\d.eE+-]+)'),
    'fn': re.compile(r'\|\s*fn\s*=\s*([\d.eE+-]+)'),
    'cmpID': re.compile(r'\|\s*cmpID\s*=\s*(\d+)'),
}

def parse_log_enhanced(filepath):
    """增强版解析：提取所有推荐指标"""
    metrics = {
        'nfev': 0,
        'distances': [],
        'choices': [],
        'penalties': [],
        'branches': set(),
        'fn_values': [],
        'cmpIDs': [],
        'extreme_count': 0,  # |dist| > 1e100
        'nan_count': 0,
        'error': None
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if not content.strip():
            metrics['error'] = 'Empty'
            return metrics
        
        # 1. NFEV: 迭代次数
        metrics['nfev'] = len(PATTERNS['iteration'].findall(content))
        
        # 2. 距离值列表 + 极端值检测
        for match in PATTERNS['distance'].findall(content):
            try:
                d = float(match)
                metrics['distances'].append(d)
                if abs(d) > 1e100 or np.isinf(d) or np.isnan(d):
                    metrics['extreme_count'] += 1
                if np.isnan(d):
                    metrics['nan_count'] += 1
            except:
                pass
        
        # 3. Choice 分布
        for c in PATTERNS['choice'].findall(content):
            metrics['choices'].append(int(c))
        
        # 4. 惩罚值
        for p in PATTERNS['penalty'].findall(content):
            try:
                metrics['penalties'].append(float(p))
            except:
                pass
        
        # 5. 唯一分支
        for inst, truth in PATTERNS['branch'].findall(content):
            metrics['branches'].add((int(inst), int(truth)))
        
        # 6. 其他辅助指标
        metrics['fn_values'] = [float(f) for f in PATTERNS['fn'].findall(content)]
        metrics['cmpIDs'] = [int(c) for c in PATTERNS['cmpID'].findall(content)]
        
    except Exception as e:
        metrics['error'] = str(e)
    
    return metrics

def compute_derived_metrics(raw):
    """从原始数据计算衍生指标"""
    result = {}
    
    # 距离统计
    if raw['distances']:
        d = np.array(raw['distances'])
        result['dist_mean'] = np.mean(d)
        result['dist_median'] = np.median(d)
        result['dist_std'] = np.std(d)
        result['dist_min'] = np.min(d)
        result['dist_max'] = np.max(d)
        result['dist_log_mean'] = np.mean(np.log1p(np.abs(d)))  # 对数域均值
    else:
        for k in ['dist_mean', 'dist_median', 'dist_std', 'dist_min', 'dist_max', 'dist_log_mean']:
            result[k] = None
    
    # Choice 分布
    if raw['choices']:
        from collections import Counter
        c = Counter(raw['choices'])
        total = len(raw['choices'])
        result['choice_guidance_rate'] = c.get(2, 0) / total  # choice=2 比例
        result['choice_new_branch_rate'] = c.get(0, 0) / total
    else:
        result['choice_guidance_rate'] = None
        result['choice_new_branch_rate'] = None
    
    # 惩罚值统计
    if raw['penalties']:
        p = np.array(raw['penalties'])
        result['penalty_mean'] = np.mean(p)
        result['penalty_final'] = p[-1] if len(p) > 0 else None
    else:
        result['penalty_mean'] = None
        result['penalty_final'] = None
    
    # 分支效率
    result['unique_branches'] = len(raw['branches'])
    if raw['nfev'] > 0:
        result['efficiency'] = len(raw['branches']) / raw['nfev']
    else:
        result['efficiency'] = None
    
    # 稳定性指标
    result['extreme_ratio'] = raw['extreme_count'] / max(1, len(raw['distances']))
    result['nan_ratio'] = raw['nan_count'] / max(1, len(raw['distances']))
    
    # 复制基础指标
    result['nfev'] = raw['nfev']
    result['error'] = raw['error']
    
    return result

# ============================================================================
# 主分析函数
# ============================================================================

def main():
    result_pattern = "output/*.log"
    output_dir = "output"
    
    strategy_names = {0: "Absolute", 1: "Relative", 3: "Normalized", 4: "Log", 99: "Auto"}
    
    # 解析所有日志
    data = []
    for log_file in sorted(glob.glob(result_pattern)):
        match = re.search(r'dist(\d+)_(\w+)', log_file)
        if not match:
            continue
        dist_id = int(match.group(1))
        
        raw = parse_log_enhanced(log_file)
        derived = compute_derived_metrics(raw)
        derived['strategy_id'] = dist_id
        derived['strategy_name'] = strategy_names.get(dist_id, f"Unknown({dist_id})")
        derived['log_file'] = os.path.basename(log_file)
        data.append(derived)
    
    df = pd.DataFrame(data)
    
    # ================= 打印核心对比表 =================
    print("\n" + "🔍 Distance Strategy Comparison".center(80))
    print("="*80)
    
    core_cols = ['strategy_name', 'nfev', 'unique_branches', 'efficiency', 
                 'choice_guidance_rate', 'dist_log_mean', 'extreme_ratio']
    
    display_df = df[core_cols].copy()
    # 格式化
    for col in ['efficiency', 'choice_guidance_rate', 'extreme_ratio']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
    if 'dist_log_mean' in display_df.columns:
        display_df['dist_log_mean'] = display_df['dist_log_mean'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    print(display_df.to_string(index=False))
    print("="*80)
    
    # ================= 可视化 1: 距离值分布（对数坐标） =================
    if 'dist_log_mean' in df.columns and df['dist_log_mean'].notna().any():
        plt.figure(figsize=(10, 6))
        plot_df = df[df['dist_log_mean'].notna()]
        sns.barplot(data=plot_df, x='strategy_name', y='dist_log_mean', palette='viridis', errorbar=None)
        plt.title('Average Distance (log(1+|d|) scale) by Strategy')
        plt.ylabel('log(1 + |distance|)')
        plt.xlabel('Distance Strategy')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/dist_log_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📈 Saved: {output_dir}/dist_log_comparison.png")
    
    # ================= 可视化 2: 引导效率 vs 分支探索 =================
    if 'choice_guidance_rate' in df.columns and 'efficiency' in df.columns:
        valid = df[(df['choice_guidance_rate'].notna()) & (df['efficiency'].notna())]
        if len(valid) >= 3:
            plt.figure(figsize=(8, 6))
            for _, row in valid.iterrows():
                plt.scatter(row['choice_guidance_rate'], row['efficiency'], 
                          label=row['strategy_name'], s=120, alpha=0.8)
            plt.xlabel('Guidance Rate (choice=2 proportion)')
            plt.ylabel('Efficiency (branches/NFEV)')
            plt.title('Strategy Effectiveness: Guidance vs Exploration')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/guidance_vs_efficiency.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"📈 Saved: {output_dir}/guidance_vs_efficiency.png")
    
    # ================= 可视化 3: 数值稳定性（极端值比例） =================
    if 'extreme_ratio' in df.columns:
        plt.figure(figsize=(10, 6))
        plot_df = df[df['extreme_ratio'].notna()]
        sns.barplot(data=plot_df, x='strategy_name', y='extreme_ratio', palette='Reds', errorbar=None)
        plt.title('Numerical Stability: Proportion of Extreme Distance Values (|d|>1e100)')
        plt.ylabel('Extreme Value Ratio')
        plt.xlabel('Distance Strategy')
        plt.xticks(rotation=45, ha='right')
        plt.yscale('log')  # 极端值比例可能很小
        plt.grid(axis='y', alpha=0.3, which='both')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/stability_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📈 Saved: {output_dir}/stability_comparison.png")
    
    # ================= 保存详细数据 =================
    df.to_csv(f'{output_dir}/detailed_results.csv', index=False)
    
    # 保存 JSON 供后续分析
    with open(f'{output_dir}/metrics.json', 'w') as f:
        json_data = []
        for _, row in df.iterrows():
            item = row.to_dict()
            # 转换 numpy 类型
            for k, v in item.items():
                if isinstance(v, (np.floating, np.integer)):
                    item[k] = float(v)
                elif isinstance(v, np.ndarray):
                    item[k] = v.tolist()
            json_data.append(item)
        json.dump(json_data, f, indent=2)
    
    # ================= 推荐最佳策略 =================
    print(f"\n🏆 Recommendations:")
    
    # 1. 最高探索效率
    if 'efficiency' in df.columns and df['efficiency'].notna().any():
        best_eff = df.loc[df['efficiency'].idxmax()]
        print(f"   • Best exploration efficiency: {best_eff['strategy_name']} "
              f"({best_eff['efficiency']:.4f} branches/NFEV)")
    
    # 2. 最稳定（极端值最少）
    if 'extreme_ratio' in df.columns and df['extreme_ratio'].notna().any():
        most_stable = df.loc[df['extreme_ratio'].idxmin()]
        print(f"   • Most numerically stable: {most_stable['strategy_name']} "
              f"(extreme ratio: {most_stable['extreme_ratio']:.2%})")
    
    # 3. 最佳引导效果
    if 'choice_guidance_rate' in df.columns and df['choice_guidance_rate'].notna().any():
        best_guide = df.loc[df['choice_guidance_rate'].idxmax()]
        print(f"   • Best guidance utilization: {best_guide['strategy_name']} "
              f"(guidance rate: {best_guide['choice_guidance_rate']:.2%})")
    
    # 4. 综合评分（简单加权）
    if all(col in df.columns for col in ['efficiency', 'choice_guidance_rate', 'extreme_ratio']):
        valid = df.dropna(subset=['efficiency', 'choice_guidance_rate', 'extreme_ratio'])
        if len(valid) > 0:
            # 归一化 + 加权: 效率(0.4) + 引导(0.4) - 极端值(0.2)
            valid = valid.copy()
            valid['score'] = (
                valid['efficiency'] / valid['efficiency'].max() * 0.4 +
                valid['choice_guidance_rate'] / valid['choice_guidance_rate'].max() * 0.4 -
                valid['extreme_ratio'] / (valid['extreme_ratio'].max() + 1e-10) * 0.2
            )
            best_overall = valid.loc[valid['score'].idxmax()]
            print(f"   • Best overall (weighted): {best_overall['strategy_name']} "
                  f"(score: {best_overall['score']:.3f})")

if __name__ == "__main__":
    # 依赖检查
    for mod in ['pandas', 'numpy', 'matplotlib', 'seaborn']:
        try:
            __import__(mod)
        except ImportError:
            print(f"❌ Missing: {mod}")
            print("💡 pip3 install pandas numpy matplotlib seaborn")
            sys.exit(1)
    
    main()