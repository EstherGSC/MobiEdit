import os
import os.path as path
import sys
import json
import random
sys.path.append('..')
from easyeditor import (
    FTHyperParams, 
    IKEHyperParams, 
    KNHyperParams, 
    MEMITHyperParams, 
    ROMEHyperParams, 
    LoRAHyperParams,
    MENDHyperParams,
    SERACHparams
    )
from easyeditor import BaseEditor
from easyeditor.models.ike import encode_ike_facts
from sentence_transformers import SentenceTransformer
from easyeditor import KnowEditDataset

import argparse
import numpy as np
import platform
import socket
import time
import hashlib
import subprocess
import torch
import transformers


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def write_json(file_path, value):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(value, file, indent=2, ensure_ascii=False, default=str)


def file_md5(file_path):
    digest = hashlib.md5()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_metadata():
    def run_git(*args):
        try:
            return subprocess.check_output(
                ["git", *args], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {
        "git_commit": run_git("rev-parse", "HEAD"),
        "git_dirty": bool(run_git("status", "--porcelain")),
    }

def eval(result_path):
    if path.exists(result_path):
        
        with open(result_path,'r') as file:
            datas=json.load(file)
        #data_rome_counterfact['post'].keys()  dict_keys(['rewrite_acc', 'locality', 'portability'])
        Edit_Succ_list=[data_rome_counterfact['post']['rewrite_acc'][0] for data_rome_counterfact in datas]
        Edit_Succ=sum(Edit_Succ_list)/len(Edit_Succ_list)*100
        print('Edit_Succ:',Edit_Succ)
        
        Portability_list=[]
        for data_rome_counterfact in datas:
            case_list=[]
            for key in data_rome_counterfact['post']['portability'].keys():
                case_list.append(sum(data_rome_counterfact['post']['portability'][key])/len(data_rome_counterfact['post']['portability'][key])*100)
            if len(case_list) != 0:
                Portability_list.append(np.mean(case_list))
        Overall_portability = np.mean(Portability_list) if Portability_list else None
        print('Overall_portability:',Overall_portability)

        Locality_list=[]
        for data_rome_counterfact in datas:
            case_list=[]
            for key in data_rome_counterfact['post']['locality'].keys():
                case_list.append(sum(data_rome_counterfact['post']['locality'][key])/len(data_rome_counterfact['post']['locality'][key])*100)
            if len(case_list) != 0:
                Locality_list.append(np.mean(case_list))
        Overall_locality = np.mean(Locality_list) if Locality_list else None
        print('Overall_locality:',Overall_locality)
        
        Fluency_list=[x['post']['fluency']['ngram_entropy'] for x in datas]
        Fluency=sum(Fluency_list)/len(Fluency_list)*100
        print('Fluency:',Fluency)
        summary = {
            "num_records": len(datas),
            "edit_success_pct": Edit_Succ,
            "rewrite_acc_mean_pct": Edit_Succ,
            "rewrite_acc_success_pct": (
                sum(value >= 1.0 for value in Edit_Succ_list)
                / len(Edit_Succ_list) * 100
            ),
            "portability_pct": Overall_portability if Portability_list else None,
            "locality_pct": Overall_locality if Locality_list else None,
            "fluency": Fluency,
        }
        write_json(os.path.join(os.path.dirname(result_path), "summary.json"), summary)
        return summary
    return {}



if __name__ == "__main__":
    print("-----begin-----")
    parser = argparse.ArgumentParser()
    parser.add_argument('--editing_method', required=True, type=str)
    parser.add_argument('--hparams_dir', required=True, type=str)
    parser.add_argument('--data_dir', required=True, type=str)
    parser.add_argument('--ds_size', default=None, type=int)
    parser.add_argument('--metrics_save_dir', default='./output', type=str)
    parser.add_argument('--datatype', default=None,type=str)
    parser.add_argument('--train_data_path', type=str)
    parser.add_argument('--pre_file', default='./seq_pre.json', type=str)
    parser.add_argument('--run_dir', default=None, type=str,
                        help='Directory for all artifacts of this run')

    args = parser.parse_args()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = args.run_dir or os.path.join(
        args.metrics_save_dir, "runs",
        f"{timestamp}_{args.editing_method}_{args.datatype or 'unknown'}",
    )
    os.makedirs(run_dir, exist_ok=True)
    args.run_dir = run_dir
    run_started = time.time()
    os.environ["MOBIEDIT_LOG_DIR"] = run_dir
    stdout_file = open(os.path.join(run_dir, "stdout.log"), "w", encoding="utf-8")
    sys.stdout = Tee(sys.stdout, stdout_file)
    sys.stderr = Tee(sys.stderr, stdout_file)
    write_json(os.path.join(run_dir, "args.json"), vars(args))
    write_json(os.path.join(run_dir, "run_metadata.json"), {
        "status": "running",
        "started_at": timestamp,
    })
    print("SEED=42")
    if os.path.isfile(args.data_dir):
        print(f"DATASET_MD5={file_md5(args.data_dir)}")

    if args.editing_method == 'FT':
        editing_hparams = FTHyperParams
    elif args.editing_method == 'IKE':
        editing_hparams = IKEHyperParams
    elif args.editing_method == 'KN':
        editing_hparams = KNHyperParams
    elif args.editing_method == 'MEMIT':
        editing_hparams = MEMITHyperParams
    elif args.editing_method == 'ROME':
        editing_hparams = ROMEHyperParams
    elif args.editing_method == 'LoRA':
        editing_hparams = LoRAHyperParams
    else:
        raise NotImplementedError
    
    # args.datatype = 'zsre'
    hparams = editing_hparams.from_hparams(args.hparams_dir)
    write_json(os.path.join(run_dir, "hparams.json"), hparams.to_dict())
    system_info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "seed": 42,
        "transformers_version": transformers.__version__,
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
        **git_metadata(),
    }
    write_json(os.path.join(run_dir, "system.json"), system_info)



    print('-----read data begin-----')
    datas = KnowEditDataset(args.data_dir,size=args.ds_size)
    print('-----read data-----')
    if args.datatype == 'counterfact' or args.datatype == 'recent' or args.datatype == 'zsre':
        print('-----zsre/counterfact----')
        prompts=[data['prompt'] for data in datas]
        subjects=[data['subject'] for data in datas]
        target_new = [data['target_new'] for data in datas]
        
        portability_r =[data['portability_r'] for data in datas]
        portability_s =[data['portability_s'] for data in datas]
        portability_l =[data['portability_l'] for data in datas]

        portability_reasoning_prompts=[]
        portability_reasoning_ans=[]
        portability_Logical_Generalization_prompts=[]
        portability_Logical_Generalization_ans=[]
        portability_Subject_Aliasing_prompts=[]
        portability_Subject_Aliasing_ans=[]
        
        portability_data = [portability_r,portability_s,portability_l]
        portability_prompts = [portability_reasoning_prompts,portability_Subject_Aliasing_prompts,portability_Logical_Generalization_prompts]
        portability_answers = [portability_reasoning_ans,portability_Subject_Aliasing_ans,portability_Logical_Generalization_ans]
        for data, portable_prompts, portable_answers in zip(portability_data,portability_prompts,portability_answers):
            for item in data:
                if item is None:
                    portable_prompts.append(None)
                    portable_answers.append(None)
                else:
                    temp_prompts = []
                    temp_answers = []
                    for pr in item:
                        prompt=pr["prompt"]
                        an=pr["ground_truth"]
                        while isinstance(an,list):
                            an = an[0]
                        if an.strip() =="":
                            continue
                        temp_prompts.append(prompt)
                        temp_answers.append(an)
                    portable_prompts.append(temp_prompts)
                    portable_answers.append(temp_answers)
        assert len(prompts) == len(portability_reasoning_prompts) == len(portability_Logical_Generalization_prompts) == len(portability_Subject_Aliasing_prompts)
        
        locality_rs = [data['locality_rs'] for data in datas]
        locality_f = [data['locality_f'] for data in datas]
        locality_Relation_Specificity_prompts=[]
        locality_Relation_Specificity_ans=[]
        locality_Forgetfulness_prompts=[]        
        locality_Forgetfulness_ans=[]
        
        locality_data = [locality_rs, locality_f]
        locality_prompts = [locality_Relation_Specificity_prompts,locality_Forgetfulness_prompts]
        locality_answers = [locality_Relation_Specificity_ans,locality_Forgetfulness_ans]
        for data, local_prompts, local_answers in zip(locality_data,locality_prompts,locality_answers):
            for item in data:
                if item is None:
                    local_prompts.append(None)
                    local_answers.append(None)
                else:
                    temp_prompts = []
                    temp_answers = []
                    for pr in item:
                        prompt=pr["prompt"]
                        an=pr["ground_truth"]
                        while isinstance(an,list):
                            an = an[0]
                        if an.strip() =="":
                            continue
                        temp_prompts.append(prompt)
                        temp_answers.append(an)
                    local_prompts.append(temp_prompts)
                    local_answers.append(temp_answers)
        assert len(prompts) == len(locality_Relation_Specificity_prompts) == len(locality_Forgetfulness_prompts)
        locality_inputs = {}
        portability_inputs = {}
        
        locality_inputs = {
            'Relation_Specificity':{
                'prompt': locality_Relation_Specificity_prompts,
                'ground_truth': locality_Relation_Specificity_ans
            },
            'Forgetfulness':{
                'prompt':locality_Forgetfulness_prompts,
                'ground_truth':locality_Forgetfulness_ans
            }
        }
        portability_inputs = {
            'Subject_Aliasing':{
                'prompt': portability_Subject_Aliasing_prompts,
                'ground_truth': portability_Subject_Aliasing_ans
            },
            'reasoning':{
                'prompt': portability_reasoning_prompts,
                'ground_truth': portability_reasoning_ans           
            },
            'Logical_Generalization':{
                'prompt': portability_Logical_Generalization_prompts,
                'ground_truth': portability_Logical_Generalization_ans           
            }
        }
    if args.datatype == 'wikibio':
        prompts=[data['prompt'] for data in datas]
        subjects=[data['subject'] for data in datas]
        target_new = [data['target_new'] for data in datas]
        
        locality_rs = [data['locality_rs'] for data in datas]
        locality_f = [data['locality_f'] for data in datas]
        locality_Relation_Specificity_prompts=[]
        locality_Relation_Specificity_ans=[]
        
        locality_data = [locality_rs]
        locality_prompts = [locality_Relation_Specificity_prompts]
        locality_answers = [locality_Relation_Specificity_ans]
        for data, local_prompts, local_answers in zip(locality_data,locality_prompts,locality_answers):
            for item in data:
                if item is None:
                    local_prompts.append(None)
                    local_answers.append(None)
                else:
                    temp_prompts = []
                    temp_answers = []
                    for pr in item:
                        prompt=pr["prompt"]
                        an=pr["ground_truth"]
                        while isinstance(an,list):
                            an = an[0]
                        if an.strip() =="":
                            continue
                        temp_prompts.append(prompt)
                        temp_answers.append(an)
                    local_prompts.append(temp_prompts)
                    local_answers.append(temp_answers)
        assert len(prompts) == len(locality_Relation_Specificity_prompts)
        portability_inputs = None
        locality_inputs = {}
        locality_inputs = {
            'Relation_Specificity':{
                'prompt': locality_Relation_Specificity_prompts,
                'ground_truth': locality_Relation_Specificity_ans
            }
        }
    # print(locality_inputs)
    hparams = editing_hparams.from_hparams(args.hparams_dir)
    # args.pre_file = f"./{hparams.model_name.split('/')[-1]}_{args.datatype}_pre_edit.json"
    if args.pre_file == './seq_pre.json':
        args.pre_file = os.path.join(
            run_dir, f"{args.data_dir.split('/')[-1]}_{args.datatype}_pre_edit.json"
        )
    # args.pre_file = f"Qwen2.5-3B-Instruct_zsre_all_pre_edit.json"
    print(args.pre_file)
    if args.pre_file is not None and os.path.exists(args.pre_file):
        pre_edit = json.load(open(args.pre_file,'r'))
        assert len(pre_edit) == len(prompts)
    else:
        pre_edit = None
    if args.editing_method == 'IKE':
        train_ds = KnowEditDataset(args.train_data_path)
        sentence_model = SentenceTransformer(hparams.sentence_model_name).to(f'cuda:{hparams.device}')
        encode_ike_facts(sentence_model, train_ds, hparams)
    else:
        train_ds = None
    model_load_start = time.time()
    editor = BaseEditor.from_hparams(hparams)
    model_load_sec = time.time() - model_load_start
    print(f"TIMING model_load_sec={model_load_sec:.6f}")
    quant_config = {
        "quantize": getattr(hparams, "quantize", None),
        "use_zo": getattr(hparams, "use_zo", None),
        "use_random_prefix": getattr(hparams, "use_random_prefix", None),
    }
    print(f"QUANT_CONFIG={quant_config if quant_config['quantize'] else 'none'}")
    if not getattr(hparams, "use_zo", False):
        print("EARLY_STOP=disabled")
    if torch.cuda.is_available():
        total_mem_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        torch.cuda.reset_peak_memory_stats()
        print(f"GPU_TOTAL_MEM_GB={total_mem_gb:.4f}")
    import multiprocessing as mp
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # 启动方式已经设置过了
    metrics, edited_model, _ = editor.edit(
        prompts=prompts,
        target_new=target_new,
        subject=subjects,
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
        train_ds=train_ds,
        keep_original_weight=True,
        pre_file=args.pre_file,
        pre_edit = pre_edit,
        test_generation=True,
    )
    result_path = os.path.join(run_dir, "metrics.json")
    write_json(result_path, metrics)
    eval(result_path)
    if torch.cuda.is_available():
        print(
            f"CUDA_PEAK_ALLOC_GB={torch.cuda.max_memory_allocated() / 1024**3:.4f} "
            f"CUDA_PEAK_RSV_GB={torch.cuda.max_memory_reserved() / 1024**3:.4f}"
        )
    write_json(os.path.join(run_dir, "run_metadata.json"), {
        "status": "completed",
        "started_at": timestamp,
        "finished_at": time.strftime("%Y%m%d_%H%M%S"),
        "total_time_sec": time.time() - run_started,
        "metrics_file": result_path,
    })
    stdout_file.close()
