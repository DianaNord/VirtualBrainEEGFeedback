using UnityEngine;
using System;

public class EventManager : MonoBehaviour
{
    public static EventManager instance;

    private void Awake()
    {
        if (instance == null)
            instance = this;
        else
            Destroy(this);
    }

    public event Action TriggerSessionStarted;
    public event Action TriggerSessionFinished;
    public event Action<string> TriggerTrialStarted;
    public event Action TriggerReference;
    public event Action<uint> TriggerCue;
    public event Action<uint> TriggerFeedback;
    public event Action TriggerTrialEnd;
    public event Action TriggerResetObjects;
    public event Action<float, bool> TriggerUpdateGlow;
    public event Action<float[]> TriggerUpdateERDS;


    public void OnTriggerSessionStarted()
    {
        TriggerSessionStarted?.Invoke();
    }
    public void OnTriggerSessionFinished()
    {
        TriggerSessionFinished?.Invoke();
    }
    public void OnTriggerTrialStarted(string condition)
    {
        TriggerTrialStarted?.Invoke(condition);
    }
    public void OnTriggerReference()
    {
        TriggerReference?.Invoke();
    }

    public void OnTriggerCue(uint condition)
    {
        TriggerCue?.Invoke(condition);
    }

    public void OnTriggerFeedback(uint condition)
    {
        TriggerFeedback?.Invoke(condition);
    }

    public void OnTriggerTrialEnd()
    {
        TriggerTrialEnd?.Invoke();
    }

    public void OnTriggerResetObjects()
    {
        TriggerResetObjects?.Invoke();
    }

    public void OnTriggerUpdateGlow(float distance, bool is_correct)
    {
        TriggerUpdateGlow?.Invoke(distance, is_correct);
    }

    public void OnTriggerUpdateERDS(float[] values)
    {
        TriggerUpdateERDS?.Invoke(values);
    }
}
