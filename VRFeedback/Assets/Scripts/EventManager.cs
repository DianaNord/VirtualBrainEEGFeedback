using UnityEngine;
using System;

/// <summary>
/// The EventManager handles event actions.
/// </summary>
public class EventManager : MonoBehaviour
{
    public static EventManager instance;

    /// <summary>
    /// Makes the class a singleton.
    /// Is called when the script object is initialised (even if the script is not enabled).
    /// </summary>
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
    public event Action<float, bool> TriggerUpdateOutline;
    public event Action<float[]> TriggerUpdateSurface;


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

    public void OnTriggerUpdateOutline(float distance, bool is_correct)
    {
        TriggerUpdateOutline?.Invoke(distance, is_correct);
    }

    public void OnTriggerUpdateSurface(float[] values)
    {
        TriggerUpdateSurface?.Invoke(values);
    }
}
