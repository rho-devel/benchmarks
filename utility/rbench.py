#!/usr/bin/python

USAGE = '''
rbench v0.1

Run benchmark of a R rbenchmark application

usage:

    $ rbench [rbench flags ...] yourBench.R your_arg1 your_arg2 ...
'''

import sys, os
import time
import argparse
import ConfigParser
from perfreport import *

def parse_cfg(utility_dir):
    config = ConfigParser.ConfigParser()
    config.read(utility_dir+'/rbench.cfg')
    rvms = []
    for rvm in config.sections():
        if (rvm != 'GENERAL'):
            rvms.append(rvm)
    
    #then change the harness file's location here
    for rvm in rvms:
        rhome = config.get(rvm, 'HOME')
        if rhome != '':
            config.set(rvm, 'CMD',  rhome + '/' + config.get(rvm, 'CMD'))
        config.set(rvm, 'HARNESS', utility_dir+'/'+config.get(rvm, 'HARNESS'))        
    
    return config, rvms


def parse_args(rvms):
    parser = argparse.ArgumentParser(description='Run a R benchmark script with a selected R VM')
    parser.add_argument('--meter', choices=['time','perf'], default='time',
                         help='''Meter used to measure the benchmark.
                         time: only measure the time in ms.
                         perf: Linux perf, only available at Linux platform''')
    parser.add_argument('--rvm', choices=rvms, default=rvms[1],
                        help='R VM used for the benchmark. Defined in rbench.cfg. Default is '+rvms[1])
    parser.add_argument('source', nargs=1,
                        help='R source file for the benchmark')
    parser.add_argument('args', nargs='*',
                        help='arguments used by the source file')
    args = parser.parse_args()
    return args

'''Return a dictionary'''
def run_bench(config, rvm, meter, source, rargs):
    warmup_rep = config.get('GENERAL', 'WARMUP_REP')
    bench_rep = config.get('GENERAL', 'BENCH_REP')
    perf_cmd = config.get('GENERAL', 'PERF_CMD')
    perf_tmp = config.get('GENERAL', 'PERF_TMP')
    env = config.get(rvm, 'ENV')
    rcmd = config.get(rvm, 'CMD')
    rcmd_args = config.get(rvm, 'ARGS')
    harness = config.get(rvm, 'HARNESS')
    harness_args = config.get(rvm, 'HARNESS_ARGS')
    
        
    if meter == 'perf':
        warmup_cmd = ' '.join([env, perf_cmd, rcmd, rcmd_args, harness, harness_args,
                               warmup_rep, source, rargs])
        bench_cmd = ' '.join([env, perf_cmd, rcmd, rcmd_args, harness, harness_args,
                               bench_rep, source, rargs])
    else: #default python
        warmup_cmd = ' '.join([env, rcmd, rcmd_args, harness, harness_args,
                               warmup_rep, source, rargs])
        bench_cmd = ' '.join([env, rcmd, rcmd_args, harness, harness_args,
                               bench_rep, source, rargs])
    
    #print warmup_cmd
    warmup_n = int(warmup_rep)
    print '[rbench]%s %s - Warmup run() %d times' % (source, rargs, warmup_n) 
    if meter == 'perf':
        with open(perf_tmp, 'w') as f:
            f.write(warmup_rep+'\n')
            
    start_t = time.time()
    warmup_exit_code = os.system(warmup_cmd)
    end_t = time.time()
    warmup_t = end_t - start_t#to ms
    
    #print bench_cmd
    bench_n = int(bench_rep)
    print '[rbench]%s %s - Bench run() %d times' % (source, rargs, bench_n) 
    if meter == 'perf':
        with open(perf_tmp, 'a') as f:
            f.write(bench_rep+'\n')
    start_t = time.time()
    bench_exit_code = os.system(bench_cmd)
    end_t = time.time()
    bench_t = end_t - start_t #to ms
    
    #finally repare return the metrix
    if meter == 'perf':
        lines = [line.strip() for line in open(perf_tmp)]
        metrics = process_perf_lines(lines)
        os.remove(perf_tmp)
    else:
        metrics = {}
        
    metrics['time'] = (bench_t -warmup_t) * 1000 / (bench_n - warmup_n)
    
    return metrics

def report(metrics, source, rargs):
    print '[rbench]%s %s - Metrics for one execution of run()' % (source, rargs) 
    keys = metrics.keys()
    keys.sort()
    for key in keys:
        print "%.2f,%s" % (metrics[key],key)

def main():
    utility_dir = os.path.dirname(os.path.realpath(__file__))
    config, rvms = parse_cfg(utility_dir)
    args = parse_args(rvms)
    
    metrics = run_bench(config, args.rvm, args.meter, args.source[0], ' '.join(args.args))
    
    #print cwd_dir
    #finally print the metrics
    report(metrics, args.source[0], ' '.join(args.args))


if __name__ == "__main__":
    main()
