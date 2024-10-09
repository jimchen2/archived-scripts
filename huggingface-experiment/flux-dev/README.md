Conclusion

1. Running inference uses around 45 GiB of Ram
2. Too few `num_inference_steps` results in grid-like images 
3. The higher the output width and height is the longer it takes for each step to infer
3. The higher the output width and height is more steps it takes to converge
4. After the image converges more inference steps are negligible
5. If `guidance_scale` is low it takes more steps to converge,
6. Using general prompts "Cozy library with many boys and girls reading", "Misty morning in a forest" makes the image very unreal, I wouldn't say these images are bad quality, but they are very fake, like paintings or illustrations. We can fix by adding specific locations like "Kensington Gardens", "Lofoten", "Shanghai" ... modern things to stop it looking like a 19th century painting, or just add "modern", "in 2024" to it. This is mainly because I think the inference on real things would be closer to realistic images it's trained on than drawings.

