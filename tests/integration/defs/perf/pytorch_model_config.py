# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -*- coding: utf-8 -*-
"""
Model pytorch yaml config for trtllm-bench perf tests
"""

from tensorrt_llm.llmapi import KvCacheConfig


def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            recursive_update(d[k], v)
        else:
            d[k] = v
    return d


def get_model_yaml_config(model_label: str,
                          lora_dirs: list[str] = None) -> dict:
    """
        Return the yaml config corresponding to the model label.
        Args:
            model_label: model label from self._config.to_string()
        Returns:
            dict: yaml config
        """
    base_config = {
        'print_iter_log': True,
        'cuda_graph_config': {
            'enable_padding': True,
        },
    }
    if 'kv_cache_dtype' in model_label:
        base_config.update({
            'kv_cache_dtype':
            model_label.split('kv_cache_dtype:')[1].split('-')[0]
        })

    # Pattern-based configurations for models matching specific substrings
    # This allows for flexible configuration of models based on naming patterns
    pattern_configs = [
        # DeepSeek R1 models with MTP speculative decoding
        {
            'patterns': [
                'deepseek_r1-bench-pytorch-float16-maxbs:1-maxnt:8192-input_output_len:1000,2000-reqs:10-ep:4-gpus:8',
                'deepseek_r1_nvfp4-bench-pytorch-float16-maxbs:1-maxnt:8192-input_output_len:1000,2000-reqs:10-ep:4-tp:8-gpus:8'
            ],
            'config': {
                'enable_attention_dp': True,
                'cuda_graph_config': {},
                'speculative_config': {
                    'decoding_type': 'MTP',
                    'num_nextn_predict_layers': 3
                }
            }
        },
        # DeepSeek R1 models with large batch sizes and cuda graph padding
        {
            'patterns': [
                'deepseek_r1_fp8-bench-pytorch-float16-maxbs:384-maxnt:1536-input_output_len:1000,2000-reqs:49152-con:3072-ep:8-gpus:8',
                'deepseek_r1_nvfp4-bench-pytorch-float16-maxbs:384-maxnt:1536-input_output_len:1000,2000-reqs:49152-con:3072-ep:8-gpus:8'
            ],
            'config': {
                'enable_attention_dp': True,
                'cuda_graph_config': {
                    'enable_padding': True,
                    'batch_sizes': [1, 2, 4, 8, 16, 32, 64, 128, 256, 384]
                }
            }
        },
        # DeepSeek R1 model with specific batch size 128
        {
            'patterns':
            'deepseek_r1_fp8-bench-pytorch-float16-maxbs:128-maxnt:1127-input_output_len:1000,2000-reqs:5120-con:1024-ep:8-gpus:8',
            'config': {
                'enable_attention_dp': True,
                'cuda_graph_config': {
                    'batch_sizes': [128]
                }
            }
        },
        # Deepseek_v3_lite_cases
        {
            'patterns':
            'deepseek_v3_lite_nvfp4-bench-pytorch-streaming-float4-maxbs:2048-maxnt:8192-input_output_len:256,256-reqs:200',
            'config': {
                'print_iter_log': True,
                'cuda_graph_config': {
                    'enable_padding': True,
                    'batch_sizes': [1, 512, 1024, 2048]
                }
            }
        },
        # Deepseek default cases
        {
            'patterns': 'deepseek_r1',
            'config': {
                'enable_attention_dp': True,
            }
        },
        # Llama Nemotron models with attention_dp disabled to prevent hangs
        {
            'patterns': [
                'llama_v3.1_nemotron_ultra_253b_fp8-bench-pytorch-float8',
                'llama_v3.3_nemotron_super_49b_fp8-bench-pytorch-float8',
                'llama_v3.3_nemotron_super_49b-bench-pytorch-bfloat16'
            ],
            'config': {
                # True causes hang, needs model-specific fix.
                'enable_attention_dp': False,
            }
        },
        # Qwen3 models with fp4 quantization on B200 and fp8 quantization on H200/H20
        {
            'patterns': [
                'qwen3_235b_a22b_fp4-bench-pytorch-float4-maxbs:512-maxnt:2048-input_output_len:1000,2000-con:512-ep:4-gpus:4',
                'qwen3_235b_a22b_fp8-bench-pytorch-float8-maxbs:512-maxnt:2048-input_output_len:1000,2000-con:256-ep:8-gpus:8'
            ],
            'config': {
                'enable_attention_dp': True,
            }
        },
        # Qwen3 models with fp4 quantization on B200 with moe backend equal to TRTLLM
        {
            'patterns': [
                'qwen3_235b_a22b_fp4-bench-pytorch-float4-maxbs:512-maxnt:2048-input_output_len:1000,2000-con:8-ep:8-gpus:8',
            ],
            'config': {
                'enable_attention_dp': False,
                'moe_config': {
                    'backend': 'TRTLLM'
                }
            }
        },
        # Llama-v3.3 models with fp8 quantization
        {
            'patterns': [
                'llama_v3.3_70b_instruct_fp8-bench-pytorch-float8-maxbs:512-maxnt:2048-input_output_len:500,2000-gpus:4',
                'llama_v3.3_70b_instruct_fp8-bench-pytorch-float8-maxbs:512-maxnt:2048-input_output_len:1000,1000-gpus:4',
                'llama_v3.3_70b_instruct_fp8-bench-pytorch-float8-maxbs:512-maxnt:2048-input_output_len:2000,500-gpus:4',
                'llama_v3.3_70b_instruct_fp8-bench-pytorch-float8-maxbs:512-maxnt:2048-input_output_len:128,128-gpus:4',
                'llama_v3.3_70b_instruct_fp8-bench-pytorch-bfloat16-maxbs:512-maxnt:2048-input_output_len:512,32-gpus:4',
                'llama_v3.1_405b_instruct_fp4',
                'llama_v4_scout_17b_16e_instruct_fp4',
                'llama_v4_maverick_17b_128e_instruct_fp8'
            ],
            'config': {
                'use_cuda_graph':
                True,
                'cuda_graph_padding_enabled':
                True,
                'cuda_graph_batch_sizes': [
                    1, 2, 4, 8, 16, 32, 64, 128, 256, 384, 512, 1024, 2048,
                    4096, 8192
                ]
            }
        }
    ]

    # Apply pattern-based configurations on top of base config
    for pattern_config in pattern_configs:
        patterns = pattern_config['patterns']
        if isinstance(patterns, str):
            patterns = [patterns]
        for pattern in patterns:
            if pattern in model_label.lower():
                recursive_update(base_config, pattern_config['config'])
                break  # Stop checking other patterns for this config once we find a match

    # lora-specific change for pytorch
    if 'pytorch' in model_label and 'loras' in model_label:
        lora_config = {
            'lora_config': {
                'lora_dir': lora_dirs if lora_dirs is not None else [],
                'max_lora_rank': 64
            }
        }
        if 'phi_4_multimodal_instruct' in model_label:
            lora_config['lora_config']['lora_target_modules'] = [
                "attn_qkv", "attn_dense", "mlp_h_to_4h", "mlp_4h_to_h"
            ]
            lora_config['lora_config']['trtllm_modules_to_hf_modules'] = {
                "attn_qkv": "qkv_proj",
                "attn_dense": "o_proj",
                "mlp_h_to_4h": "gate_up_proj",
                "mlp_4h_to_h": "down_proj"
            }
            lora_config['lora_config']['max_lora_rank'] = 64
        base_config.update(lora_config)

    kv_cache_config = base_config.get('kv_cache_config', KvCacheConfig())
    if 'kv_cache_dtype' in base_config:
        kv_cache_config.dtype = base_config.pop('kv_cache_dtype', 'auto')
        base_config.update({'kv_cache_config': kv_cache_config})

    return base_config
